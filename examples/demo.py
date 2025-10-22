"""
Example usage of WebResearcher

This script demonstrates how to use the WebResearcher library
both programmatically and through the Gradio web interface.
"""

from webresearcher import WebResearcher


def example_basic_usage():
    """Demonstrate basic usage of WebResearcher."""
    print("=" * 60)
    print("WebResearcher - Basic Usage Example")
    print("=" * 60)
    
    # Create a researcher instance
    researcher = WebResearcher(model="default", max_steps=10)
    
    # Perform research
    query = "What are the key trends in artificial intelligence?"
    print(f"\nResearch Question: {query}\n")
    
    result = researcher.research(query)
    
    # Display results
    print(f"Model: {result['model']}")
    print(f"Timestamp: {result['timestamp']}\n")
    
    print("Research Steps:")
    print("-" * 60)
    for step in result['steps']:
        print(f"\nStep {step['step']}: {step['action']}")
        print(f"  {step['detail']}")
    
    print("\n" + "=" * 60)
    print("Conclusion:")
    print("=" * 60)
    print(result['conclusion'])
    
    print("\n" + "=" * 60)
    print(f"Total research items in history: {len(researcher.get_history())}")
    print("=" * 60)


def example_web_ui():
    """Launch the Gradio web interface."""
    print("\n" + "=" * 60)
    print("Launching Gradio Web UI...")
    print("=" * 60)
    print("\nThe web interface will be available at:")
    print("  Local: http://localhost:7860")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    from webresearcher.app import main
    main()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        # Launch web UI
        example_web_ui()
    else:
        # Run basic example
        example_basic_usage()
        
        print("\n\nTo launch the web UI, run:")
        print("  python examples/demo.py web")
        print("\nOr directly:")
        print("  python -m webresearcher.app")
