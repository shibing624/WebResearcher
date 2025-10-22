"""Gradio Web UI for WebResearcher"""

import gradio as gr
from webresearcher import WebResearcher


def create_ui():
    """Create and configure the Gradio interface for WebResearcher."""
    
    # Initialize the researcher
    researcher = WebResearcher()
    
    def perform_research(query, model_choice, max_steps):
        """
        Perform research and return formatted results.
        
        Args:
            query: The research question
            model_choice: Selected model
            max_steps: Maximum reasoning steps
            
        Returns:
            Formatted research results
        """
        if not query.strip():
            return "Please enter a research question.", ""
        
        # Update researcher settings
        researcher.model = model_choice
        researcher.max_steps = max_steps
        
        # Perform research
        result = researcher.research(query)
        
        # Format the steps
        steps_text = f"## Research Process for: {result['query']}\n\n"
        steps_text += f"**Model:** {result['model']} | **Timestamp:** {result['timestamp']}\n\n"
        steps_text += "### Reasoning Steps:\n\n"
        
        for step in result['steps']:
            steps_text += f"**Step {step['step']}: {step['action']}**\n"
            steps_text += f"{step['detail']}\n\n"
        
        # Format conclusion
        conclusion_text = f"### Final Conclusion\n\n{result['conclusion']}"
        
        return steps_text, conclusion_text
    
    def get_research_history():
        """Get and format research history."""
        history = researcher.get_history()
        if not history:
            return "No research history yet."
        
        history_text = "## Research History\n\n"
        for i, item in enumerate(history, 1):
            history_text += f"### {i}. {item['query']}\n"
            history_text += f"**Model:** {item['model']} | **Time:** {item['timestamp']}\n\n"
        
        return history_text
    
    def clear_research_history():
        """Clear research history."""
        researcher.clear_history()
        return "History cleared.", ""
    
    # Create the Gradio interface
    with gr.Blocks(title="WebResearcher - AI Research Assistant") as demo:
        gr.Markdown(
            """
            # 🔬 WebResearcher
            ### Unleashing unbounded reasoning capability in Long-Horizon Agents
            
            Enter your research question below and watch the AI agent break it down into 
            multiple reasoning steps to provide comprehensive insights.
            """
        )
        
        with gr.Tab("Research"):
            with gr.Row():
                with gr.Column(scale=2):
                    query_input = gr.Textbox(
                        label="Research Question",
                        placeholder="e.g., What are the key trends in artificial intelligence for 2024?",
                        lines=3
                    )
                    
                    with gr.Row():
                        model_dropdown = gr.Dropdown(
                            choices=["default", "advanced", "fast"],
                            value="default",
                            label="Model"
                        )
                        max_steps_slider = gr.Slider(
                            minimum=3,
                            maximum=20,
                            value=10,
                            step=1,
                            label="Max Reasoning Steps"
                        )
                    
                    with gr.Row():
                        research_btn = gr.Button("🔍 Start Research", variant="primary")
                        clear_btn = gr.Button("🗑️ Clear")
            
            with gr.Row():
                with gr.Column():
                    steps_output = gr.Markdown(label="Research Process")
                with gr.Column():
                    conclusion_output = gr.Markdown(label="Conclusion")
        
        with gr.Tab("History"):
            history_output = gr.Markdown()
            with gr.Row():
                refresh_history_btn = gr.Button("🔄 Refresh History")
                clear_history_btn = gr.Button("🗑️ Clear History")
        
        # Event handlers
        research_btn.click(
            fn=perform_research,
            inputs=[query_input, model_dropdown, max_steps_slider],
            outputs=[steps_output, conclusion_output]
        )
        
        clear_btn.click(
            fn=lambda: ("", "", ""),
            outputs=[query_input, steps_output, conclusion_output]
        )
        
        refresh_history_btn.click(
            fn=get_research_history,
            outputs=history_output
        )
        
        clear_history_btn.click(
            fn=clear_research_history,
            outputs=[history_output, conclusion_output]
        )
        
        # Add examples
        gr.Examples(
            examples=[
                ["What are the latest developments in quantum computing?"],
                ["How does machine learning impact healthcare?"],
                ["What are the environmental benefits of renewable energy?"],
                ["Explain the future of autonomous vehicles"],
            ],
            inputs=query_input
        )
    
    return demo


def main():
    """Launch the Gradio web interface."""
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    main()
