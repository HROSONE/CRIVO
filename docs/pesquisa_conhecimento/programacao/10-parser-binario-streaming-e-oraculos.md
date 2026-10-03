# Parser incremental: framing, limites e equivalência

## Formato escolhido
Cada mensagem é `uint32 big endian tamanho` seguida de exatamente tamanho bytes. Tamanho zero é mensagem válida. EOF fora da fronteira é erro. maxFrame limita payload individual antes de allocation. O parser não decodifica texto; isso pertence ao protocolo superior.

[FrameDecoder](exemplos/engenharia.mjs) mantém header de quatro bytes, quantidade lida, payload em construção e posição. feed retorna frames completos; o conteúdo pode começar em qualquer offset do chunk. end confirma que não ficou prefixo incompleto. Erro de framing/limite torna decoder terminal.

## Prova por estado
No estado header, `0 <= headerUsed <= 4`. Ao completar header, size é lido na endian declarada e validado antes da alocação. No estado payload, `0 <= payloadUsed <= size <= maxFrame`. Cada iteração consome bytes ou transita depois de header completo. Frame completo volta ao estado header vazio.

Este contrato evita espera por payload gigante declarado e erro por tratar chunk como mensagem. Não fornece ressincronização após frame inválido: continuar em offset incerto pode reinterpretar payload como header. Se protocolo exigir recuperação, definir delimiter/checksum/framing que a permita e testar explicitamente.

## Memória e ownership
Payload é copiado para buffer próprio. Alterar chunk de entrada depois de feed não modifica frame entregue. Cópia custa O(n) em bytes. Uma versão zero-copy requer ownership/lifetime do backing buffer; subarray sozinho compartilha memória.

maxFrame não limita memória da lista de frames retornados por um chunk enorme contendo muitas mensagens. Limitar chunk/total externamente, devolver iterator ou emitir frames com backpressure são opções. FrameDecoder não abre sockets e não implementa deadline de peer que envia header e nunca envia body.

## UTF-8 está em outra camada
Texto pode ter caractere dividido entre chunks. TextDecoder com stream preserva bytes incompletos; fatal determina rejeição/substituição de invalid encoding. Antes de parse JSON, definir limites de bytes e estrutura. Um tamanho válido do frame não garante conteúdo válido ou regra de negócio.

## Oráculo independente
Para mensagens fixas conhecidas, encodeFrame gera representação do protocolo. Testes com expected bytes verificam todos pontos de divisão, sequência de mensagens incluindo zero-length, byte a byte, EOF parcial e header acima do limite. Também verificam ausência de alias com input.

Não basta testar encode e decode e aceitar roundtrip: os dois podem compartilhar erro de endian. Por isso a interpretação de header/limite é testada com bytes literais e expected definido. Para próxima extensão, comparar com implementação independente e fuzz com limites de execução.

## Produção
Definir versão do protocolo, máximo agregado, autenticação, encoding, compressão, frame type, correlation ID, checksum se apropriado, comportamento de EOF e limites de concorrência. TLS protege transporte; não valida tamanho/schema ou autorização da mensagem.

**Relações:** js_framing, fronteira_streaming-parsers, redes_tcp, testes_parser-equivalence.

