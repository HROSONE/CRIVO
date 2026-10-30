/*
 * Motor do CRIVO em C: o mesmo Transformer de linguagem_profunda.py (GPT-2: posição aprendida, LayerNorm antes de
 * cada parte, atenção causal, MLP com GELU exata, saída com a matriz de embedding), com os pesos em int8 por linha
 * NA MEMÓRIA (o NumPy multiplica tudo de volta para float32: 4 vezes mais RAM) e as contas em vários núcleos.
 *
 * Não tem modelo de ninguém: só lê os pesos próprios do CRIVO, num arquivo feito por motor_nativo.py a partir do
 * pesos_numpy.npz conferido pelo SHA. Serve para qualquer tamanho (camadas, dimensão, cabeças, vocabulário e
 * contexto vêm do arquivo). A escolha da palavra (freio de repetição, palavras proibidas) continua no Python.
 *
 * Os núcleos trabalham por threads simples do sistema (pthreads), sem OpenMP: o OpenMP estático dentro de uma
 * biblioteca aberta pelo Python (dlopen) é um gatilho conhecido de queda ao criar threads no Android, e no servidor
 * dispensa a libgomp. As threads nascem uma vez, em crivo_abrir, e esperam trabalho. "#pragma omp simd" só pede ao
 * compilador para vetorizar as somas (com -fopenmp-simd, que não usa biblioteca nenhuma).
 *
 * API (ctypes):
 *   void *crivo_abrir(const char *arquivo, int threads)   NULL se o arquivo não servir
 *   int   crivo_info(void *m, int *v)                      v = {vocabulario, dimensao, camadas, cabecas, contexto}
 *   int   crivo_avancar(void *m, const int *ids, int n, int inicio, float *logits)
 *         estados das posições inicio..inicio+n-1 (inicio=0 recomeça o cache); logits da última posição (vocabulário)
 *   void  crivo_fechar(void *m)
 */
#include <math.h>
#include <pthread.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

#define MAGICO "CRIVOM1"
#define LINHAS_BLOCO 16   /* linhas de peso por bloco na conta do prompt (matmul) */
#define MAX_THREADS 16
#define ESPERA_ATIVA 2000    /* voltas olhando a geração (cedendo a CPU) antes de dormir na condição */

typedef struct { const int8_t *q; const float *s; int linhas, colunas; } Mat;
typedef struct { const float *n1w, *n1b, *n2w, *n2b, *b0, *b2; Mat qkv, proj, m0, m2; } Bloco;

struct Motor;
typedef void (*Tarefa)(struct Motor *m, void *arg, int quem, int ini, int fim);

typedef struct Motor {
    int V, D, L, H, C, threads;
    Mat emb, pos;
    Bloco *bl;
    const float *nw, *nb;
    float *kc, *vc;                   /* cache: [camada][posição][D] */
    float *x, *h, *qkv, *att, *mlp;   /* rascunho para até C posições */
    float *linhas, *notas;            /* por thread: LINHAS_BLOCO linhas de peso em float e as notas da atenção */
    void *mapa; size_t tam;
    /* as threads que ajudam (a que chama crivo_avancar é a número 0) */
    pthread_t ajudantes[MAX_THREADS];
    int n_ajudantes, sair;
    pthread_mutex_t trava;
    pthread_cond_t tem_trabalho, acabou;
    volatile int geracao;             /* muda a cada trabalho novo */
    volatile int faltam;              /* ajudantes que ainda não terminaram o trabalho corrente */
    Tarefa tarefa; void *arg; int total;
} Motor;

static void faixa(int total, int partes, int i, int *ini, int *fim) {
    *ini = (int)((long long)total * i / partes);
    *fim = (int)((long long)total * (i + 1) / partes);
}

static void *ajudante(void *p) {
    Motor *m = ((void **)p)[0];
    int quem = (int)(intptr_t)((void **)p)[1];
    free(p);
    int vista = 0;
    for (;;) {
        int g, voltas = 0;
        while ((g = __atomic_load_n(&m->geracao, __ATOMIC_ACQUIRE)) == vista && !__atomic_load_n(&m->sair, __ATOMIC_ACQUIRE)) {
            if (++voltas < ESPERA_ATIVA) { sched_yield(); continue; }
            pthread_mutex_lock(&m->trava);
            while (__atomic_load_n(&m->geracao, __ATOMIC_ACQUIRE) == vista && !m->sair)
                pthread_cond_wait(&m->tem_trabalho, &m->trava);
            pthread_mutex_unlock(&m->trava);
        }
        if (__atomic_load_n(&m->sair, __ATOMIC_ACQUIRE)) return NULL;
        vista = g;
        int ini, fim;
        faixa(m->total, m->threads, quem, &ini, &fim);
        if (ini < fim) m->tarefa(m, m->arg, quem, ini, fim);
        if (__atomic_sub_fetch(&m->faltam, 1, __ATOMIC_ACQ_REL) == 0) {
            pthread_mutex_lock(&m->trava);
            pthread_cond_signal(&m->acabou);
            pthread_mutex_unlock(&m->trava);
        }
    }
}

/* Divide [0, total) entre as threads (a que chama faz a parte 0) e só volta quando todas terminam. */
static void paralelo(Motor *m, int total, Tarefa tarefa, void *arg) {
    if (m->n_ajudantes == 0 || total < 2) { tarefa(m, arg, 0, 0, total); return; }
    m->tarefa = tarefa; m->arg = arg; m->total = total;
    __atomic_store_n(&m->faltam, m->n_ajudantes, __ATOMIC_RELEASE);
    pthread_mutex_lock(&m->trava);
    __atomic_add_fetch(&m->geracao, 1, __ATOMIC_ACQ_REL);
    pthread_cond_broadcast(&m->tem_trabalho);
    pthread_mutex_unlock(&m->trava);
    int ini, fim;
    faixa(total, m->threads, 0, &ini, &fim);
    if (ini < fim) tarefa(m, arg, 0, ini, fim);
    int voltas = 0;
    while (__atomic_load_n(&m->faltam, __ATOMIC_ACQUIRE) > 0) {
        if (++voltas < ESPERA_ATIVA) { sched_yield(); continue; }
        pthread_mutex_lock(&m->trava);
        while (__atomic_load_n(&m->faltam, __ATOMIC_ACQUIRE) > 0) pthread_cond_wait(&m->acabou, &m->trava);
        pthread_mutex_unlock(&m->trava);
    }
}

static const uint8_t *ler_mat(const uint8_t *p, Mat *m, int linhas, int colunas) {
    size_t n = (size_t)linhas * colunas;
    m->q = (const int8_t *)p; m->linhas = linhas; m->colunas = colunas;
    p += (n + 3) & ~(size_t)3;        /* alinhado em 4 bytes */
    m->s = (const float *)p;
    return p + (size_t)linhas * sizeof(float);
}

static const uint8_t *ler_vet(const uint8_t *p, const float **v, int n) {
    *v = (const float *)p;
    return p + (size_t)n * sizeof(float);
}

void crivo_fechar(void *mm) {
    Motor *m = (Motor *)mm;
    if (!m) return;
    if (m->n_ajudantes > 0) {
        pthread_mutex_lock(&m->trava);
        __atomic_store_n(&m->sair, 1, __ATOMIC_RELEASE);
        pthread_cond_broadcast(&m->tem_trabalho);
        pthread_mutex_unlock(&m->trava);
        for (int i = 0; i < m->n_ajudantes; i++) pthread_join(m->ajudantes[i], NULL);
    }
    pthread_mutex_destroy(&m->trava); pthread_cond_destroy(&m->tem_trabalho); pthread_cond_destroy(&m->acabou);
    free(m->bl); free(m->kc); free(m->vc); free(m->x); free(m->h); free(m->qkv); free(m->att); free(m->mlp);
    free(m->linhas); free(m->notas);
    if (m->mapa) munmap(m->mapa, m->tam);
    free(m);
}

void *crivo_abrir(const char *arquivo, int threads) {
    int fd = open(arquivo, O_RDONLY);
    if (fd < 0) return NULL;
    struct stat st;
    if (fstat(fd, &st) != 0 || st.st_size < 32) { close(fd); return NULL; }
    void *mapa = mmap(NULL, (size_t)st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if (mapa == MAP_FAILED) return NULL;
    const uint8_t *p = (const uint8_t *)mapa;
    if (memcmp(p, MAGICO, 8) != 0) { munmap(mapa, (size_t)st.st_size); return NULL; }
    const int32_t *cab = (const int32_t *)(p + 8);
    Motor *m = (Motor *)calloc(1, sizeof(Motor));
    if (!m) { munmap(mapa, (size_t)st.st_size); return NULL; }
    pthread_mutex_init(&m->trava, NULL); pthread_cond_init(&m->tem_trabalho, NULL); pthread_cond_init(&m->acabou, NULL);
    m->mapa = mapa; m->tam = (size_t)st.st_size;
    m->V = cab[0]; m->D = cab[1]; m->L = cab[2]; m->H = cab[3]; m->C = cab[4];
    m->threads = threads > 0 ? (threads > MAX_THREADS ? MAX_THREADS : threads) : 4;
    if (m->V <= 0 || m->D <= 0 || m->L <= 0 || m->H <= 0 || m->C <= 0 || m->D % m->H) { crivo_fechar(m); return NULL; }
    int D = m->D, C = m->C;
    p += 8 + 5 * 4;
    p = ler_mat(p, &m->emb, m->V, D);
    p = ler_mat(p, &m->pos, C, D);
    m->bl = (Bloco *)calloc((size_t)m->L, sizeof(Bloco));
    if (!m->bl) { crivo_fechar(m); return NULL; }
    for (int c = 0; c < m->L; c++) {
        Bloco *b = &m->bl[c];
        p = ler_vet(p, &b->n1w, D); p = ler_vet(p, &b->n1b, D);
        p = ler_mat(p, &b->qkv, 3 * D, D);
        p = ler_mat(p, &b->proj, D, D);
        p = ler_vet(p, &b->n2w, D); p = ler_vet(p, &b->n2b, D);
        p = ler_mat(p, &b->m0, 4 * D, D); p = ler_vet(p, &b->b0, 4 * D);
        p = ler_mat(p, &b->m2, D, 4 * D); p = ler_vet(p, &b->b2, D);
    }
    p = ler_vet(p, &m->nw, D); p = ler_vet(p, &m->nb, D);
    if ((size_t)(p - (const uint8_t *)mapa) != m->tam) { crivo_fechar(m); return NULL; }   /* tamanho tem de bater */
    size_t cache = (size_t)m->L * C * D;
    m->kc = (float *)malloc(cache * sizeof(float)); m->vc = (float *)malloc(cache * sizeof(float));
    m->x = (float *)malloc((size_t)C * D * sizeof(float)); m->h = (float *)malloc((size_t)C * D * sizeof(float));
    m->qkv = (float *)malloc((size_t)C * 3 * D * sizeof(float)); m->att = (float *)malloc((size_t)C * D * sizeof(float));
    m->mlp = (float *)malloc((size_t)C * 4 * D * sizeof(float));
    m->linhas = (float *)malloc((size_t)m->threads * LINHAS_BLOCO * 4 * D * sizeof(float));
    m->notas = (float *)malloc((size_t)m->threads * C * sizeof(float));
    if (!m->kc || !m->vc || !m->x || !m->h || !m->qkv || !m->att || !m->mlp || !m->linhas || !m->notas) { crivo_fechar(m); return NULL; }
    for (int i = 1; i < m->threads; i++) {
        void **arg = (void **)malloc(2 * sizeof(void *));
        if (!arg) break;
        arg[0] = m; arg[1] = (void *)(intptr_t)i;
        if (pthread_create(&m->ajudantes[m->n_ajudantes], NULL, ajudante, arg) != 0) { free(arg); break; }
        m->n_ajudantes++;
    }
    m->threads = m->n_ajudantes + 1;   /* se alguma não nasceu, o trabalho é dividido entre as que existem */
    return m;
}

int crivo_info(void *mm, int *v) {
    Motor *m = (Motor *)mm;
    v[0] = m->V; v[1] = m->D; v[2] = m->L; v[3] = m->H; v[4] = m->C;
    return 0;
}

static float soma_prod(const float *a, const float *b, int n) {
    float s = 0;
    #pragma omp simd reduction(+:s)
    for (int j = 0; j < n; j++) s += a[j] * b[j];
    return s;
}

static float soma_prod_q8(const float *a, const int8_t *q, int n) {
    float s = 0;
    #pragma omp simd reduction(+:s)
    for (int j = 0; j < n; j++) s += a[j] * (float)q[j];
    return s;
}

/* Quatro produtos de uma vez: a mesma linha de peso w contra quatro posições (cada valor de w é lido uma vez para as
 * quatro), com quatro somas independentes que o compilador vetoriza. */
static void soma_prod4(const float *w, const float *x0, const float *x1, const float *x2, const float *x3, int n,
                       float *r) {
    float s0 = 0, s1 = 0, s2 = 0, s3 = 0;
    #pragma omp simd reduction(+:s0, s1, s2, s3)
    for (int j = 0; j < n; j++) {
        float a = w[j];
        s0 += a * x0[j]; s1 += a * x1[j]; s2 += a * x2[j]; s3 += a * x3[j];
    }
    r[0] = s0; r[1] = s1; r[2] = s2; r[3] = s3;
}

typedef struct { const float *X; int n; const Mat *W; const float *vies; float *Y; } ArgMat;

/* Uma palavra: produto direto com o int8 (lê 4 vezes menos memória que o float32), linhas ini..fim. */
static void tarefa_vetor(Motor *m, void *p, int quem, int ini, int fim) {
    const ArgMat *a = (const ArgMat *)p;
    int entrada = a->W->colunas;
    (void)m; (void)quem;
    for (int o = ini; o < fim; o++)
        a->Y[o] = a->W->s[o] * soma_prod_q8(a->X, a->W->q + (size_t)o * entrada, entrada) + (a->vies ? a->vies[o] : 0.0f);
}

/* Várias palavras (o prompt), em blocos de LINHAS_BLOCO linhas do peso (blocos ini..fim): o bloco passa para float uma
 * vez e serve a todas as posições, quatro por vez. Assim as quatro posições ficam no cache da CPU enquanto servem às
 * LINHAS_BLOCO linhas (antes, cada linha relia o prompt inteiro). */
static void tarefa_blocos(Motor *m, void *p, int quem, int ini, int fim) {
    const ArgMat *a = (const ArgMat *)p;
    const Mat *W = a->W;
    int entrada = W->colunas, saida = W->linhas, n = a->n;
    float *painel = m->linhas + (size_t)quem * LINHAS_BLOCO * 4 * m->D;
    for (int bl = ini; bl < fim; bl++) {
        int o0 = bl * LINHAS_BLOCO, no = saida - o0 < LINHAS_BLOCO ? saida - o0 : LINHAS_BLOCO;
        for (int i = 0; i < no; i++) {
            const int8_t *q = W->q + (size_t)(o0 + i) * entrada;
            float *l = painel + (size_t)i * entrada;
            for (int j = 0; j < entrada; j++) l[j] = (float)q[j];
        }
        int t = 0;
        for (; t + 4 <= n; t += 4) {
            const float *x0 = a->X + (size_t)t * entrada, *x1 = x0 + entrada, *x2 = x1 + entrada, *x3 = x2 + entrada;
            for (int i = 0; i < no; i++) {
                int o = o0 + i;
                float r[4], s = W->s[o], b = a->vies ? a->vies[o] : 0.0f;
                soma_prod4(painel + (size_t)i * entrada, x0, x1, x2, x3, entrada, r);
                for (int k = 0; k < 4; k++) a->Y[(size_t)(t + k) * saida + o] = s * r[k] + b;
            }
        }
        for (; t < n; t++)
            for (int i = 0; i < no; i++) {
                int o = o0 + i;
                a->Y[(size_t)t * saida + o] = W->s[o] * soma_prod(painel + (size_t)i * entrada, a->X + (size_t)t * entrada, entrada)
                                              + (a->vies ? a->vies[o] : 0.0f);
            }
    }
}

/* Y[t][o] = escala[o] * <X[t], W[o]> (+ vies[o]), t < n. */
static void matmul(Motor *m, const float *X, int n, const Mat *W, const float *vies, float *Y) {
    ArgMat a = {X, n, W, vies, Y};
    if (n == 1) paralelo(m, W->linhas, tarefa_vetor, &a);
    else paralelo(m, (W->linhas + LINHAS_BLOCO - 1) / LINHAS_BLOCO, tarefa_blocos, &a);
}

static void norma(const float *x, const float *w, const float *b, float *y, int D) {
    float media = 0, var = 0;
    for (int j = 0; j < D; j++) media += x[j];
    media /= D;
    for (int j = 0; j < D; j++) { float d = x[j] - media; var += d * d; }
    var /= D;
    float inv = 1.0f / sqrtf(var + 1e-5f);
    for (int j = 0; j < D; j++) y[j] = (x[j] - media) * inv * w[j] + b[j];
}

/* A mesma erf do NumPy do CRIVO (pontuador_frases._erf, Abramowitz & Stegun 7.1.26). */
static float gelu(float x) {
    float z = x / 1.41421356237f, a = fabsf(z), t = 1.0f / (1.0f + 0.3275911f * a);
    float y = 1.0f - (((((1.061405429f * t - 1.453152027f) * t) + 1.421413741f) * t - 0.284496736f) * t + 0.254829592f) * t * expf(-a * a);
    return 0.5f * x * (1.0f + (z < 0 ? -y : y));
}

typedef struct { const float *kc, *vc; int inicio; float escala; } ArgAtencao;

/* Atenção causal de cada par (posição t, cabeça hh), numerados t * H + hh, de ini a fim. */
static void tarefa_atencao(Motor *m, void *p, int quem, int ini, int fim) {
    const ArgAtencao *a = (const ArgAtencao *)p;
    int D = m->D, H = m->H, hd = D / H;
    float *sc = m->notas + (size_t)quem * m->C;
    for (int i = ini; i < fim; i++) {
        int t = i / H, hh = i % H, total = a->inicio + t + 1;
        const float *q = m->qkv + (size_t)t * 3 * D + hh * hd;
        float maior = -INFINITY;
        for (int u = 0; u < total; u++) {
            sc[u] = soma_prod(q, a->kc + (size_t)u * D + hh * hd, hd) * a->escala;
            if (sc[u] > maior) maior = sc[u];
        }
        float soma = 0;
        for (int u = 0; u < total; u++) { sc[u] = expf(sc[u] - maior); soma += sc[u]; }
        float *o = m->att + (size_t)t * D + hh * hd;
        for (int j = 0; j < hd; j++) o[j] = 0;
        for (int u = 0; u < total; u++) {
            float w = sc[u] / soma;
            const float *v = a->vc + (size_t)u * D + hh * hd;
            for (int j = 0; j < hd; j++) o[j] += w * v[j];
        }
    }
}

int crivo_avancar(void *mm, const int *ids, int n, int inicio, float *logits) {
    Motor *m = (Motor *)mm;
    int D = m->D, H = m->H, hd = D / H, C = m->C;
    if (n <= 0 || inicio < 0 || inicio + n > C) return -1;
    for (int t = 0; t < n; t++) if (ids[t] < 0 || ids[t] >= m->V) return -2;
    for (int t = 0; t < n; t++) {
        const int8_t *e = m->emb.q + (size_t)ids[t] * D, *pp = m->pos.q + (size_t)(inicio + t) * D;
        float se = m->emb.s[ids[t]], sp = m->pos.s[inicio + t];
        for (int j = 0; j < D; j++) m->x[(size_t)t * D + j] = se * e[j] + sp * pp[j];
    }
    float escala = 1.0f / sqrtf((float)hd);
    for (int c = 0; c < m->L; c++) {
        const Bloco *b = &m->bl[c];
        float *kc = m->kc + (size_t)c * C * D, *vc = m->vc + (size_t)c * C * D;
        for (int t = 0; t < n; t++) norma(m->x + (size_t)t * D, b->n1w, b->n1b, m->h + (size_t)t * D, D);
        matmul(m, m->h, n, &b->qkv, NULL, m->qkv);
        for (int t = 0; t < n; t++) {
            memcpy(kc + (size_t)(inicio + t) * D, m->qkv + (size_t)t * 3 * D + D, (size_t)D * sizeof(float));
            memcpy(vc + (size_t)(inicio + t) * D, m->qkv + (size_t)t * 3 * D + 2 * D, (size_t)D * sizeof(float));
        }
        ArgAtencao at = {kc, vc, inicio, escala};
        paralelo(m, n * H, tarefa_atencao, &at);
        matmul(m, m->att, n, &b->proj, NULL, m->h);
        for (size_t i = 0; i < (size_t)n * D; i++) m->x[i] += m->h[i];
        for (int t = 0; t < n; t++) norma(m->x + (size_t)t * D, b->n2w, b->n2b, m->h + (size_t)t * D, D);
        matmul(m, m->h, n, &b->m0, b->b0, m->mlp);
        for (size_t i = 0; i < (size_t)n * 4 * D; i++) m->mlp[i] = gelu(m->mlp[i]);
        matmul(m, m->mlp, n, &b->m2, b->b2, m->h);
        for (size_t i = 0; i < (size_t)n * D; i++) m->x[i] += m->h[i];
    }
    norma(m->x + (size_t)(n - 1) * D, m->nw, m->nb, m->h, D);
    matmul(m, m->h, 1, &m->emb, NULL, logits);
    return 0;
}
