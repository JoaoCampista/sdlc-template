---
id: DESIGN-F-<DOMINIO>-V1
kind: design
title: Design — F-<DOMINIO>-V1
parent: F-<DOMINIO>-V1
version: 0.1.0
status: draft
applicable: true
last_updated: <YYYY-MM-DD>
---

# Design — estado por estado

Contrato de implementação visual; não substitui a spec. Se não houver UI, use `applicable: false` e justifique em Referências; mantenha as demais seções com “não se aplica”.

## Referências
- Spec e versão: <path e versão>.
- Referência visual: <link com node/frame ou artefato local versionado>.
- Superfícies e variantes: <plataformas, breakpoints, temas, idiomas>.
- Componentes existentes e implementação: <caminhos>.
- Tokens e fonte canônica: <path; direção da geração e comando>.
- Responsável pela revisão: <papel>.

Spec decide comportamento, fluxo e texto; referência visual decide aparência. Divergência não autoriza inventar: registre abaixo e resolva com o responsável antes da implementação afetada.

## Estado por estado
Uma linha por estado e variante relevante; incluir inicial, carregamento, sucesso, vazio, erro, sem permissão, offline e recuperação quando aplicáveis. Justificar variantes não aplicáveis.

| Estado / AC | Superfície / variante | Referência visual | Componentes / tokens | Texto e ação | Teclado / foco / acessibilidade |
|---|---|---|---|---|---|
| <estado> | <variante> | <link> | <componentes> | <texto> | <comportamento> |

## Diferenças conhecidas
| Diferença spec × referência | Decisão / fonte vencedora | Responsável | Status |
|---|---|---|---|

## Lacunas
Estados sem referência; referências sem estado; decisões ainda não tomadas. Lacuna bloqueante não pode ser preenchida silenciosamente pelo construtor.

## Conferência visual
Build verde não prova aparência nem acessibilidade. Abra e inspecione cada captura; depois exercite interação, foco e tecnologia assistiva conforme as ACs. Separe “inspecionado em imagem” de “testado interativamente”.

| Estado / variante | Build ou commit | Evidência persistente | Referência comparada | Resultado / revisor / data |
|---|---|---|---|---|
| <estado> | <commit> | docs/images/F-ID-estado-variante.png | <frame> | pendente |

Não use caminhos temporários como única evidência. Não inclua dados pessoais nas capturas. A task fecha com evidência e revisão registrada, ou fica explicitamente pendente.
