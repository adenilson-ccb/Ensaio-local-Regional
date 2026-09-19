import re
import unicodedata
import streamlit as st
from datetime import date

import db

st.set_page_config(page_title="Ensaio Local", page_icon="🎵", layout="wide")

DIAS_SEMANA = [
    "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sábado", "Domingo",
]

CORDAS = ["violino", "viola", "violoncelo"]
MADEIRAS = [
    "flauta", "clarinete", "clarone", "sax_soprano", "sax_alto", "sax_tenor",
    "sax_baritono", "oboe", "oboe_damore", "corne_ingles", "clarinete_alto",
]
METAIS = [
    "trompete", "trombone", "flugelhorn", "euphonium", "tuba",
    "trompete_cornet", "trompa", "trombonito", "baritono_pisto", "sax_horn",
]
MINISTERIO = [
    "anciaes", "diaconos", "coop_of_ministerial", "coop_jovens_menores",
    "enc_regionais", "enc_locais", "examinadoras",
]

LABELS = {
    "violino": "Violino", "viola": "Viola", "violoncelo": "Violoncelo",
    "flauta": "Flauta", "clarinete": "Clarinete", "clarone": "Clarone",
    "sax_soprano": "Sax Soprano", "sax_alto": "Sax Alto", "sax_tenor": "Sax Tenor",
    "sax_baritono": "Sax Barítono", "oboe": "Oboé", "oboe_damore": "Oboé D'Amore",
    "corne_ingles": "Corne Inglês", "clarinete_alto": "Clarinete Alto",
    "trompete": "Trompete", "trombone": "Trombone", "flugelhorn": "Flugelhorn",
    "euphonium": "Euphonium", "tuba": "Tuba", "trompete_cornet": "Trompete Cornet",
    "trompa": "Trompa", "trombonito": "Trombonito", "baritono_pisto": "Barítono pisto",
    "sax_horn": "Sax Horn",
    "anciaes": "Anciães", "diaconos": "Diáconos",
    "coop_of_ministerial": "Coop. do Of. Ministerial",
    "coop_jovens_menores": "Coop. de Jovens e Menores",
    "enc_regionais": "Enc. Regionais", "enc_locais": "Enc. Locais",
    "examinadoras": "Examinadoras",
}

META_CORDAS, META_MADEIRAS, META_METAIS = 0.50, 0.25, 0.25

CORES = {
    "Cordas": "#2563EB",    # azul
    "Madeiras": "#16A34A",  # verde
    "Metais": "#EA580C",    # laranja
}

DATA_PADRAO = date(2026, 9, 19)


def cabecalho_colorido(titulo: str, cor: str):
    st.markdown(
        f"""<div style="background-color:{cor}; padding:10px 16px; border-radius:6px; margin:12px 0 8px 0;">
        <span style="color:white; font-weight:600; font-size:1.05rem;">{titulo}</span>
        </div>""",
        unsafe_allow_html=True,
    )


def cartao_percentual(titulo, cor, valor, meta):
    st.markdown(
        f"""<div style="border:2px solid {cor}; border-radius:8px; padding:10px 14px; text-align:center;">
        <div style="color:{cor}; font-weight:600;">{titulo}</div>
        <div style="font-size:1.6rem; font-weight:700;">{valor:.0%}</div>
        <div style="font-size:0.8rem; color:#666;">meta: {meta:.0%}</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ---------------- Login com senha compartilhada ----------------

def checar_login():
    if st.session_state.get("autenticado"):
        return True

    st.title("🎵 Ensaio Local")
    senha = st.text_input("Senha de acesso", type="password")
    if st.button("Entrar"):
        if senha == st.secrets.get("APP_PASSWORD"):
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    return False


# ---------------- Geração de PDF do resumo ----------------

def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def formatar_hinos(texto: str) -> str:
    """Se forem só números (separados por vírgula, espaço ou hífen), mostra 62-278-391...
    Caso contrário, mantém o texto como foi digitado."""
    texto = (texto or "").strip()
    if not texto:
        return ""
    partes = [p for p in re.split(r"[,;\s\-]+", texto) if p]
    if partes and all(p.isdigit() for p in partes):
        return "-".join(partes)
    return texto


def contexto_pdf_do_registro(e: dict) -> dict:
    """Monta o contexto do PDF a partir de um registro (salvo ou vindo do formulário)."""
    data_str = e.get("data") or ""
    try:
        data_str = date.fromisoformat(e.get("data")).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        pass

    def qtd(campo):
        return int(e.get(campo) or 0)

    encarregados = [
        (e.get(f"nome_encarregado_{i}") or "", e.get(f"localidade_{i}") or "")
        for i in range(1, 4)
    ]

    total_cordas = sum(qtd(c) for c in CORDAS)
    total_madeiras = sum(qtd(c) for c in MADEIRAS)
    total_metais = sum(qtd(c) for c in METAIS)
    acordeon = qtd("acordeon")
    total_musicos = total_cordas + total_madeiras + total_metais + acordeon

    instrumentos = [(LABELS[c], qtd(c)) for c in CORDAS + MADEIRAS + METAIS if qtd(c) > 0]
    if acordeon:
        instrumentos.append(("Harmônico (Acordeon)", acordeon))
    instrumentos.sort(key=lambda item: _sem_acento(item[0]))

    def pct(valor):
        return valor / total_musicos if total_musicos else 0

    composicao = [
        ("Cordas", total_cordas, pct(total_cordas), META_CORDAS),
        ("Madeiras", total_madeiras, pct(total_madeiras), META_MADEIRAS),
        ("Metais", total_metais, pct(total_metais), META_METAIS),
    ]

    organistas = qtd("organistas")
    irmaos = qtd("irmaos")
    irmas = qtd("irmas")

    return {
        "data_str": data_str,
        "dia_semana": e.get("dia_semana") or "",
        "tipo_ensaio": e.get("tipo_ensaio") or "",
        "encarregados": encarregados,
        "instrumentos": instrumentos,
        "composicao": composicao,
        "total_musicos": total_musicos,
        "organistas": organistas,
        "irmaos": irmaos,
        "irmas": irmas,
        "total_geral": total_musicos + organistas + irmaos + irmas,
        "hinos": formatar_hinos(e.get("hinos_ensaiados")),
    }


def gerar_pdf(ctx: dict) -> bytes:
    from fpdf import FPDF
    from fpdf.fonts import FontFace

    LARGURA = 120        # largura das tabelas (mm)
    RECUO = 25           # recuo das tabelas à esquerda (mm)
    ALTURA_LINHA = 4.2   # altura de cada linha de tabela (mm)
    PADDING = 0.9
    cabecalho_estilo = FontFace(emphasis="", fill_color=(240, 240, 240))
    negrito = FontFace(emphasis="B")

    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    def tabela(titulo, linhas, larguras, cabecalho=None, negrito_em=()):
        """Título + tabela. Se não couber no resto da página, vai inteira para a próxima."""
        n_linhas = len(linhas) + (1 if cabecalho else 0)
        altura = 13 + n_linhas * (ALTURA_LINHA + 2 * PADDING)
        if pdf.get_y() + altura > pdf.h - pdf.b_margin:
            pdf.add_page()

        pdf.ln(4)
        pdf.set_font("Helvetica", "BI", 10.5)
        pdf.cell(0, 7, titulo, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.5)

        pdf.set_x(pdf.l_margin + RECUO)
        pdf.set_font("Helvetica", "", 8)
        with pdf.table(
            width=LARGURA, col_widths=larguras, align="L", line_height=ALTURA_LINHA,
            borders_layout="ALL", first_row_as_headings=False, padding=PADDING,
        ) as t:
            if cabecalho:
                r = t.row()
                for c in cabecalho:
                    r.cell(c, style=cabecalho_estilo)
            for i, linha in enumerate(linhas):
                r = t.row()
                for c in linha:
                    r.cell(str(c), style=negrito if i in negrito_em else None)

    # Título
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, f"Culto de Jovens - Ensaio {ctx['tipo_ensaio']}".strip(), align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Ensaio", new_x="LMARGIN", new_y="NEXT")

    # Encarregados
    enc = [(n or "-", l or "-") for n, l in ctx["encarregados"] if n or l]
    if enc:
        tabela("Encarregados", enc, (50, 50), cabecalho=("Nome", "Localidade"))

    # Músicos e Organistas
    n = len(ctx["instrumentos"])
    linhas = list(ctx["instrumentos"]) + [
        ("Sub Total (músicos)", ctx["total_musicos"]),
        ("Organistas (Órgão)", ctx["organistas"]),
        ("Sub Total (músicos + organistas)", ctx["total_musicos"] + ctx["organistas"]),
    ]
    tabela("Músicos e Organistas", linhas, (72, 28),
           cabecalho=("Instrumento", "Quantidade"), negrito_em={n, n + 1, n + 2})

    # Composição dos participantes
    comp = [(nome, qtd, f"{pc:.0%}", f"{meta:.0%}") for nome, qtd, pc, meta in ctx["composicao"]]
    tabela("Composição dos participantes", comp, (34, 22, 22, 22),
           cabecalho=("Categoria", "Cadastrados", "% atual", "Meta CCB"))

    # Hinos ensaiados
    if ctx["hinos"]:
        pdf.ln(4)
        pdf.set_font("Helvetica", "BI", 10.5)
        pdf.cell(0, 7, "Hinos ensaiados", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5.5, ctx["hinos"], new_x="LMARGIN", new_y="NEXT")

    # Irmandade
    total_irmandade = ctx["irmaos"] + ctx["irmas"]
    tabela("Irmandade", [
        ("Irmãos", ctx["irmaos"]),
        ("Irmãs", ctx["irmas"]),
        ("Total de Irmandade", total_irmandade),
    ], (72, 28), negrito_em={2})

    # Resumo
    tabela("Resumo", [
        ("Quant. de Músicos", ctx["total_musicos"]),
        ("Quant. Organistas", ctx["organistas"]),
        ("Total", ctx["total_musicos"] + ctx["organistas"]),
        ("Total de Irmandade", total_irmandade),
        ("TOTAL GERAL", ctx["total_geral"]),
    ], (72, 28), negrito_em={2, 4})

    return bytes(pdf.output())


# ---------------- Formulário reaproveitável (Novo Registro e Edição) ----------------

def formulario_ensaio(key_prefix: str, valores: dict | None = None):
    """Desenha todos os campos do Ensaio. Se 'valores' for passado (um registro
    já salvo), os campos vêm preenchidos com esses valores — usado na edição."""
    valores = valores or {}

    opcoes_tipo = ["Local", "Regional"]
    tipo_atual = valores.get("tipo_ensaio")
    tipo_ensaio = st.selectbox(
        "Ensaio Local e Regional",
        opcoes_tipo,
        index=opcoes_tipo.index(tipo_atual) if tipo_atual in opcoes_tipo else 0,
        key=f"{key_prefix}_tipo_ensaio",
    )

    data_inicial = DATA_PADRAO
    if valores.get("data"):
        try:
            data_inicial = date.fromisoformat(valores["data"])
        except ValueError:
            pass

    data_ensaio = st.date_input(
        "Data do Ensaio",
        value=data_inicial,
        format="DD/MM/YYYY",
        key=f"{key_prefix}_data_ensaio",
    )
    dia_semana = DIAS_SEMANA[data_ensaio.weekday()]
    st.caption(f"Dia da semana: {dia_semana}")

    fora_padrao = dia_semana not in ("Quinta-feira", "Domingo", "Segunda-feira")
    if fora_padrao:
        st.info("Esse dia está fora do padrão habitual de ensaios — será marcado como tal.")

    st.subheader("Encarregados")
    st.caption("Quem vai reger a localidade de cada um.")
    encarregados = []
    for i in range(1, 4):
        col_a, col_b = st.columns(2)
        nome = col_a.text_input(
            f"Nome {i} — Nome do encarregado",
            value=valores.get(f"nome_encarregado_{i}") or "",
            key=f"{key_prefix}_nome_encarregado_{i}",
        )
        localidade = col_b.text_input(
            f"Localidade {i} — Localidade",
            value=valores.get(f"localidade_{i}") or "",
            key=f"{key_prefix}_localidade_{i}",
        )
        encarregados.append((nome, localidade))

    st.subheader("Músicos")

    cabecalho_colorido("Cordas", CORES["Cordas"])
    valores_cordas = {}
    cols = st.columns(len(CORDAS))
    for i, campo in enumerate(CORDAS):
        valores_cordas[campo] = cols[i].number_input(
            LABELS[campo], min_value=0, step=1,
            value=int(valores.get(campo) or 0), key=f"{key_prefix}_{campo}",
        )
    total_cordas = sum(valores_cordas.values())
    st.caption(f"Total cordas: {total_cordas}")

    cabecalho_colorido("Madeiras", CORES["Madeiras"])
    valores_madeiras = {}
    cols = st.columns(4)
    for i, campo in enumerate(MADEIRAS):
        valores_madeiras[campo] = cols[i % 4].number_input(
            LABELS[campo], min_value=0, step=1,
            value=int(valores.get(campo) or 0), key=f"{key_prefix}_{campo}",
        )
    total_madeiras = sum(valores_madeiras.values())
    st.caption(f"Total madeiras: {total_madeiras}")

    cabecalho_colorido("Metais", CORES["Metais"])
    valores_metais = {}
    cols = st.columns(4)
    for i, campo in enumerate(METAIS):
        valores_metais[campo] = cols[i % 4].number_input(
            LABELS[campo], min_value=0, step=1,
            value=int(valores.get(campo) or 0), key=f"{key_prefix}_{campo}",
        )
    total_metais = sum(valores_metais.values())
    st.caption(f"Total metais: {total_metais}")

    with st.expander("Harmônico", expanded=False):
        acordeon = st.number_input(
            "Harmônico (Acordeon)", min_value=0, step=1,
            value=int(valores.get("acordeon") or 0), key=f"{key_prefix}_acordeon",
        )
        st.caption(f"Total harmônico: {acordeon}")

    organistas = st.number_input(
        "Organistas", min_value=0, step=1,
        value=int(valores.get("organistas") or 0), key=f"{key_prefix}_organistas",
    )

    total_musicos = total_cordas + total_madeiras + total_metais + acordeon

    st.subheader("Ministério")
    st.caption("Não entra na soma de Total Geral — fica só para conferência.")
    valores_ministerio = {}
    cols = st.columns(4)
    for i, campo in enumerate(MINISTERIO):
        valores_ministerio[campo] = cols[i % 4].number_input(
            LABELS[campo], min_value=0, step=1,
            value=int(valores.get(campo) or 0), key=f"{key_prefix}_{campo}",
        )
    total_ministerio = sum(valores_ministerio.values())
    st.caption(f"Total Ministério: {total_ministerio}")

    st.subheader("Irmandade")
    col1, col2 = st.columns(2)
    irmaos = col1.number_input(
        "Irmãos", min_value=0, step=1,
        value=int(valores.get("irmaos") or 0), key=f"{key_prefix}_irmaos",
    )
    irmas = col2.number_input(
        "Irmãs", min_value=0, step=1,
        value=int(valores.get("irmas") or 0), key=f"{key_prefix}_irmas",
    )
    st.caption(f"Total de Irmandade: {irmaos + irmas}")

    st.subheader("Composição dos participantes")
    st.caption("Referência sugerida pela CCB: 50% Cordas, 25% Madeiras, 25% Metais.")
    pc_cordas = (total_cordas / total_musicos) if total_musicos else 0
    pc_madeiras = (total_madeiras / total_musicos) if total_musicos else 0
    pc_metais = (total_metais / total_musicos) if total_musicos else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        cartao_percentual("Cordas", CORES["Cordas"], pc_cordas, META_CORDAS)
    with c2:
        cartao_percentual("Madeiras", CORES["Madeiras"], pc_madeiras, META_MADEIRAS)
    with c3:
        cartao_percentual("Metais", CORES["Metais"], pc_metais, META_METAIS)

    hinos = st.text_area(
        "Hinos ensaiados", placeholder="Ex: Hino 10 - ...\nHino 25 - ...",
        value=valores.get("hinos_ensaiados") or "", key=f"{key_prefix}_hinos",
    )

    st.subheader("Resumo")
    r1, r2, r3 = st.columns(3)
    r1.metric("Quant. de Músicos", total_musicos)
    r2.metric("Quant. Organistas", organistas)
    r3.metric("Total", total_musicos + organistas)

    total_geral = total_musicos + organistas + irmaos + irmas
    st.metric("Total Geral (Músicos + Organistas + Irmandade)", total_geral)
    st.caption("O Ministério não entra nessa soma — fica só para conferência.")

    dados = {
        "data": data_ensaio.isoformat(),
        "dia_semana": dia_semana,
        "tipo_ensaio": tipo_ensaio,
        "nome_encarregado_1": encarregados[0][0], "localidade_1": encarregados[0][1],
        "nome_encarregado_2": encarregados[1][0], "localidade_2": encarregados[1][1],
        "nome_encarregado_3": encarregados[2][0], "localidade_3": encarregados[2][1],
        "fora_do_padrao": 1 if fora_padrao else 0,
        "irmaos": irmaos,
        "irmas": irmas,
        **valores_cordas,
        **valores_madeiras,
        **valores_metais,
        "acordeon": acordeon,
        "organistas": organistas,
        **valores_ministerio,
        # Campo removido da tela; a coluna continua no banco (mantém o valor antigo, se houver).
        "visitantes": int(valores.get("visitantes") or 0),
        "hinos_ensaiados": hinos,
    }

    contexto_pdf = contexto_pdf_do_registro(dados)

    return dados, contexto_pdf


# ---------------- Tela: Novo Registro ----------------

def tela_novo_registro():
    st.header("Novo Registro de Ensaio")

    dados, contexto_pdf = formulario_ensaio("novo")

    b1, b2 = st.columns(2)
    if b1.button("Salvar Ensaio", type="primary", use_container_width=True, key="novo_salvar"):
        db.salvar_ensaio(dados, [])
        st.success("Registro salvo com sucesso!")
        st.rerun()

    pdf_bytes = gerar_pdf(contexto_pdf)
    b2.download_button(
        "Salvar em PDF",
        data=pdf_bytes,
        file_name=f"ensaio_{dados['data']}.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="novo_download_pdf",
    )


# ---------------- Tela: Histórico ----------------

def tela_historico():
    st.header("Histórico de Ensaios")
    mostrar_fora_padrao = st.checkbox("Mostrar também datas fora do padrão", value=True)

    ensaios = db.listar_ensaios(limite=50)
    if not mostrar_fora_padrao:
        ensaios = [e for e in ensaios if not e.get("fora_do_padrao")]

    if not ensaios:
        st.info("Nenhum registro ainda.")
        return

    for e in ensaios:
        total_musicos = sum(e.get(campo, 0) or 0 for campo in CORDAS + MADEIRAS + METAIS) + (e.get("acordeon") or 0)
        tipo = e.get("tipo_ensaio") or ""
        titulo = f"{e['dia_semana']} — {e['data']}"
        if tipo:
            titulo += f" · {tipo}"
        titulo += f" · {total_musicos + (e.get('organistas') or 0)} presente(s)"

        with st.expander(titulo):
            for i in range(1, 4):
                nome = e.get(f"nome_encarregado_{i}")
                localidade = e.get(f"localidade_{i}")
                if nome or localidade:
                    st.write(f"**Encarregado {i}:** {nome or '-'} · **Localidade:** {localidade or '-'}")
            st.write(f"**Irmãos:** {e.get('irmaos')} · **Irmãs:** {e.get('irmas')}")
            st.write(f"**Músicos:** {total_musicos} · **Organistas:** {e.get('organistas')}")
            if e.get("hinos_ensaiados"):
                st.write("**Hinos ensaiados:**")
                st.text(e["hinos_ensaiados"])

            st.divider()

            col_pdf, col_editar = st.columns(2)

            pdf_bytes = gerar_pdf(contexto_pdf_do_registro(e))
            col_pdf.download_button(
                "📄 Baixar em PDF",
                data=pdf_bytes,
                file_name=f"ensaio_{e.get('data')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_{e['id']}",
            )

            editando_key = f"editando_{e['id']}"
            rotulo_editar = "✖️ Fechar edição" if st.session_state.get(editando_key) else "✏️ Editar este registro"
            if col_editar.button(rotulo_editar, use_container_width=True, key=f"btn_editar_{e['id']}"):
                st.session_state[editando_key] = not st.session_state.get(editando_key, False)
                st.rerun()

            if st.session_state.get(editando_key):
                st.markdown("---")
                st.subheader("Editando registro")
                dados_editados, _ = formulario_ensaio(f"editar_{e['id']}", valores=e)

                if st.button("💾 Salvar alterações", type="primary", key=f"salvar_edicao_{e['id']}"):
                    db.atualizar_ensaio(e["id"], dados_editados)
                    st.success("Registro atualizado com sucesso!")
                    st.session_state[editando_key] = False
                    st.rerun()


# ---------------- Main ----------------

def main():
    if not checar_login():
        return

    db.init_db()

    aba1, aba2 = st.tabs(["📝 Novo Registro", "📜 Histórico"])
    with aba1:
        tela_novo_registro()
    with aba2:
        tela_historico()


if __name__ == "__main__":
    main()
