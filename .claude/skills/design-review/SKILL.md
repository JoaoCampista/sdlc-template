---
name: design-review
description: Confere uma UI por estados, variantes, referência visual, acessibilidade e evidência persistente, sem impor stack ou identidade visual.
argument-hint: "F-ID [estado ou superfície]"
allowed-tools: Read, Grep, Glob
---

1. Leia spec e design.md da feature; confirme versão, estados, variantes e fonte visual aceita. Esta skill orienta revisão; não cria convenção DS nem autoriza edição de produto.
2. Diferencie regra normativa do projeto, recomendação externa e hipótese não verificada. Documentação de plataforma deve ter fonte, versão consultada e disponibilidade da API. Não atribua recomendação comunitária ao fabricante.
3. Confira cada referência visual contra imagem real persistida e commit/build correto. Se não há acesso à imagem ou interação, declare a limitação; não dê aprovado com base só no nome do arquivo.
4. Confira carregamento, vazio, erro, sucesso, recuperação e permissão quando aplicáveis; layout, texto, tokens, foco, ordem e rótulos. Sugira previews determinísticos por estado com dados fictícios, sem rede.
5. Exercícios interativos de teclado, leitor de tela, tamanho de texto, contraste e movimento reduzido precisam de evidência própria. A captura não os substitui.
6. Registre achados com estado, variante, AC, esperado/observado e referência. A implementação deve atualizar design.md e suas tasks com a revisão e pendências. Não copie cores, tipografia, animações ou plataformas de outro produto.
