"""Hugging Face Space: Privacy Seed · Detector LGPD."""

import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

from pathlib import Path  # noqa: E402

import gradio as gr  # noqa: E402
import lgpd_views as views  # noqa: E402

from privacyseed_lgpd import Detector  # noqa: E402

detector = Detector()
detector.analyze("Aquecimento do modelo.")  # load the model once, at startup


def run(text: str):
    text, cut = views.truncate(text or "")
    result = detector.analyze(text)  # never logged or stored
    status = f"Texto truncado em {views.MAX_CHARS} caracteres." if cut else ""
    return (
        result.anonymized,
        views.legal_rows(result),
        views.highlighted(text, result),
        result.to_dict(),
        status,
    )


with gr.Blocks(title="Privacy Seed · Detector LGPD", analytics_enabled=False) as demo:
    gr.Markdown("# Privacy Seed · Detector LGPD")
    gr.Markdown(views.NOTICE)
    text_in = gr.Textbox(label="Texto de entrada", lines=8, max_length=views.MAX_CHARS)
    gr.Examples(examples=views.load_examples(Path(__file__).parent / "examples"), inputs=text_in)
    button = gr.Button("Anonimizar", variant="primary")
    status = gr.Markdown()
    with gr.Tabs():
        with gr.Tab("Visão jurídica"):
            anonymized = gr.Textbox(label="Texto anonimizado", lines=8)
            table = gr.Dataframe(headers=views.LEGAL_HEADERS, interactive=False)
        with gr.Tab("Visão técnica"):
            spans = gr.HighlightedText(label="Spans detectados")
            raw = gr.JSON(label="Resultado (JSON)")
            gr.Code(views.USAGE, language="python", label="Uso local")
    gr.Markdown(views.DISCLAIMER)
    gr.Markdown(views.CTA)
    # private: not listed in the API docs and not callable by Gradio clients.
    button.click(run, inputs=text_in, outputs=[anonymized, table, spans, raw, status], api_visibility="private")

if __name__ == "__main__":
    demo.launch()
