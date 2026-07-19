# NovaStore Cloud Demo V5

Versão personalizável da aplicação para minicurso de Computação em Nuvem.

## Produto principal

ASUS ROG Swift OLED PG34WCDM.

A V5 inclui ilustrações locais provisórias para que a aplicação funcione sem depender
de imagens externas. Substitua os arquivos pelos materiais que você escolher.

## Personalização

Edite:

```text
data/store.json
```

Você pode alterar:

- nome da loja;
- título normal;
- título da Black Friday;
- descrições;
- produto principal;
- nomes dos produtos;
- imagens;
- preços normais;
- preços promocionais;
- avaliações;
- quantidade de avaliações;
- selos;
- parcelamento.

## Imagens

Substitua:

```text
static/images/hero/asus-rog-pg34wcdm-normal.svg
static/images/hero/asus-rog-pg34wcdm-black-friday.svg
static/images/products/*.svg
```

Você pode usar arquivos `.webp`, desde que também atualize os caminhos em
`data/store.json`.

Recomendação:

- banner: 1600 × 900;
- produtos: 800 × 800;
- formato WebP;
- fundo limpo;
- imagens otimizadas.

## Executar

```bash
docker compose up --build
```

Acesse:

```text
http://localhost:8081
```

## Aviso

Loja fictícia para fins educacionais. Produtos, preços, avaliações e promoções são
meramente ilustrativos.


## Novidades da V6

- visual inspirado em lojas premium;
- banner maior e mais limpo;
- cards de produtos mais compactos;
- navegação por categorias;
- notificações durante a demonstração;
- alerta de CPU elevada;
- aviso de novo servidor detectado;
- rodapé de portfólio com tecnologias utilizadas.


## V6 Final

Esta versão combina:

- banner visual da V4;
- sem preço, avaliação ou parcelamento no banner;
- imagem configurável do ASUS ROG Swift OLED PG34WCDM;
- textos genéricos da loja;
- cards, notificações e rodapé da V6;
- catálogo configurável por JSON;
- carga controlada da V4.1.

### Imagem do banner

Coloque a imagem escolhida em:

```text
static/images/hero/banner-monitor.png
```

O mesmo arquivo é utilizado no modo normal e no modo Black Friday.

Caso ainda não tenha o PNG, altere temporariamente em `data/store.json`:

```json
"image_normal": "/static/images/hero/banner-monitor.svg",
"image_black_friday": "/static/images/hero/banner-monitor.svg"
```


## Ajustes da V6 Final 1

- monitor maior no banner;
- selo de estoque removido;
- máscara visual para ocultar o selo CES incorporado ao PNG;
- brilho vermelho ampliado no modo Black Friday;
- marca-d’água mais visível;
- botões maiores;
- painel renomeado para “Painel da demonstração”;
- contagem final 3–2–1 em tela cheia;
- transições de aproximadamente 700 ms.
