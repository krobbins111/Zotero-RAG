import gradio as gr

from conversation import handle_user_query, create_conversation
from zotero_connector import embed_all_pdfs, test_connection


with gr.Blocks() as zotero_ui:

    with gr.Row(
        variant='compact'
    ):
        user_id = gr.components.Textbox(label='Zotero User Id')
        api_key = gr.components.Textbox(label='Zotero API key')
        result_zotero = gr.components.Textbox(label='Zotero Connection Status')
    
    test_connection_btn = gr.components.Button(value='Search')
    test_connection_btn.click(
        test_connection,
        [user_id, api_key],
        [result_zotero]
    )

    with gr.Row(
        variant='compact'
    ):
        search_input = gr.components.Textbox(label='Zotero Tags (comma separated)')
        result_input = gr.components.Textbox(label='Download status')
    
    search_btn = gr.components.Button(value='Search')
    search_btn.click(
        embed_all_pdfs,
        [search_input, user_id, api_key],
        [result_input]
    )
    print(result_input)
    chatbot = gr.Chatbot(label='Chat With Your Lit Review', bubble_full_width=False, height=600)
    msg = gr.Textbox(label='Query', placeholder='Enter text and press enter')
    clear = gr.ClearButton([msg, chatbot], variant='stop')

    msg.submit(
        handle_user_query,
        [msg, chatbot],
        [msg, chatbot]
    ).then(
        create_conversation,
        [chatbot],
        [chatbot]
    )

demo = gr.TabbedInterface(
    [zotero_ui],
    ['Lit Review of the Future']
)

demo.queue()
