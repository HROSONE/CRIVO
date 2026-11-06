/*
 * Motor do CRIVO em C: o mesmo Transformer de linguagem_profunda.py (GPT-2: posição aprendida, LayerNorm antes de
 * cada parte, atenção causal, MLP com GELU exata, saída com a matriz de embedding), com os pesos em int8 por linha
 * NA MEMÓRIA (o NumPy multiplica tudo de volta para float32: 4 vezes mais RAM) e as contas em vários núcleos.
 *
 * Não tem modelo de ninguém: só lê os pesos próprios do CRIVO, num arquivo feito por motor_nativo.py a partir do
 * pesos_numpy.npz conferido pelo SHA. Serve para qualquer tamanho (camadas, dimensão, cabeças, vocabulário e
 * contexto vêm do arquivo). A escolha da palavra (freio de repetição, palavras proibidas) continua no Python.
 *
 * API (ctypes):
 *   void *crivo_abrir(const char *arquivo, int threads)   NULL se o arquivo não servir
 *   int   crivo_info(void *m, int *v)                      v = {vocabulario, dimensao, camadas, cabecas, contexto}
 *   int   crivo_avancar(void *m, const int *ids, int n, int inicio, float *logits)
 *         estados das posições inicio..inicio+n-1 (inicio=0 recomeça o cache); logits da última posição (vocabulário)
 *   void  crivo_fechar(void *m)
 */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#ifdef _OPENMP
#include <omp.h>
#endif

#define MAGICO "CRIVOM1"

typedef struct { const int8_t *q; const float *s; int linhas, colunas; } Mat;
typedef struct { const float *n1w, *n1b, *n2w, *n2b, *b0, *b2; Mat qkv, proj, m0, m2; } Bloco;

typedef struct {
    int V, D, L, H, C, threads;
    Mat emb, pos;
    Bloco *bl;
    const float *nw, *nb;
    float *kc, *vc;                   /* cache: [camada][posição][D] */
    float *x, *h, *qkv, *att, *mlp;   /* rascunho para até C posições */
    float *linhas, *notas;            /* por thread: uma linha de peso em float e as notas da atenção */
    void *mapa; size_t tam;
} Motor;

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
    m->mapa = mapa; m->tam = (size_t)st.st_size;
    m->V = cab[0]; m->D = cab[1]; m->L = cab[2]; m->H = cab[3]; m->C = cab[4];
    m->threads = threads > 0 ? threads : 4;
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
    m->linhas = (float *)malloc((size_t)m->threads * 4 * D * sizeof(float));
    m->notas = (float *)malloc((size_t)m->threads * C * sizeof(float));
    if (!m->kc || !m->vc || !m->x || !m->h || !m->qkv || !m->att || !m->mlp || !m->linhas || !m->notas) { crivo_fechar(m); return NULL; }
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

static int thread_atual(void) {
#ifdef _OPENMP
    return omp_get_thread_num();
#else
    return 0;
#endif
}

/* Y[t][o] = escala[o] * <X[t], W[o]> (+ vies[o]), t < n. Uma palavra: produto direto com o int8 (lê 4 vezes menos
 * memória que o float32). Várias (o prompt): cada linha do peso vira float uma vez e serve a todas as posições. */
static void matmul(const Motor *m, const float *X, int n, const Mat *W, const float *vies, float *Y) {
    int entrada = W->colunas, saida = W->linhas;
    if (n == 1) {
        #pragma omp parallel for schedule(static) num_threads(m->threads)
        for (int o = 0; o < saida; o++)
            Y[o] = W->s[o] * soma_prod_q8(X, W->q + (size_t)o * entrada, entrada) + (vies ? vies[o] : 0.0f);
        return;
    }
    #pragma omp parallel for schedule(static) num_threads(m->threads)
    for (int o = 0; o < saida; o++) {
        float *linha = m->linhas + (size_t)thread_atual() * 4 * m->D;
        const int8_t *q = W->q + (size_t)o * entrada;
        for (int j = 0; j < entrada; j++) linha[j] = (float)q[j];
        float s = W->s[o], b = vies ? vies[o] : 0.0f;
        for (int t = 0; t < n; t++) Y[(size_t)t * saida + o] = s * soma_prod(linha, X + (size_t)t * entrada, entrada) + b;
    }
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
        #pragma omp parallel for collapse(2) schedule(static) num_threads(m->threads)
        for (int t = 0; t < n; t++) {
            for (int hh = 0; hh < H; hh++) {
                int total = inicio + t + 1;
                const float *q = m->qkv + (size_t)t * 3 * D + hh * hd;
                float *sc = m->notas + (size_t)thread_atual() * C;
                float maior = -INFINITY;
                for (int u = 0; u < total; u++) {
                    sc[u] = soma_prod(q, kc + (size_t)u * D + hh * hd, hd) * escala;
                    if (sc[u] > maior) maior = sc[u];
                }
                float soma = 0;
                for (int u = 0; u < total; u++) { sc[u] = expf(sc[u] - maior); soma += sc[u]; }
                float *o = m->att + (size_t)t * D + hh * hd;
                for (int j = 0; j < hd; j++) o[j] = 0;
                for (int u = 0; u < total; u++) {
                    float w = sc[u] / soma;
                    const float *v = vc + (size_t)u * D + hh * hd;
                    for (int j = 0; j < hd; j++) o[j] += w * v[j];
                }
            }
        }
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
