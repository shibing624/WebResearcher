# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Main entry point for WebResearcher agent

Supports two modes:
1. Single Agent (default): Fast, cost-effective, suitable for most scenarios
2. TTS (Test-Time Scaling): 3-5x cost, higher accuracy, for critical scenarios
"""
import argparse
import asyncio
import json
from loguru import logger
from dotenv import load_dotenv

load_dotenv('.env', override=True)


async def main(args):
    # 1. 定义 LLM 配置
    llm_config = {
        "model": args.model,
        "generate_cfg": {
            'max_input_tokens': args.max_input_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "presence_penalty": args.presence_penalty,
        }
    }
    
    # Only add model_thinking_type if explicitly set by user (not default)
    if hasattr(args, 'model_thinking_type') and args.model_thinking_type != 'disabled':
        llm_config["generate_cfg"]["model_thinking_type"] = args.model_thinking_type

    # 2. 选择代理模式
    if args.use_webweaver:
        logger.info("✅ Using WebWeaver dual-agent mode (dynamic outline)")
        from webresearcher.web_weaver_agent import WebWeaverAgent
        agent = WebWeaverAgent(llm_config=llm_config, function_list=args.function_list)
        mode = 'webweaver'
        use_tts_mode = False
    elif args.use_tts:
        logger.warning("=" * 80)
        logger.warning("⚠️  Test-Time Scaling (TTS) Mode Enabled")
        logger.warning(f"   Cost: ~{args.num_parallel_agents + 0.5:.1f}x of single-agent baseline")
        logger.warning(f"   Running {args.num_parallel_agents} parallel agents")
        logger.warning("   Use this ONLY for high-value scenarios!")
        logger.warning("=" * 80)
        
        from webresearcher.tts_agent import TestTimeScalingAgent
        agent = TestTimeScalingAgent(
            llm_config=llm_config,
            function_list=args.function_list,
        )
        mode = 'tts'
        use_tts_mode = True
    else:
        logger.info("✅ Using single-agent mode (cost-effective)")
        from webresearcher.web_researcher_agent import WebResearcherAgent
        agent = WebResearcherAgent(
            llm_config=llm_config,
            function_list=args.function_list,
        )
        mode = 'single'
        use_tts_mode = False

    # 3. 准备输入数据 (与原始的 `run` 格式一致)
    input_data = [
        {
            "question": "请根据以下线索找出这位艺术家的姓名：曾在中国中央美术学院及德国杜塞尔多夫艺术学院深造，并赴德国留学。在德国学习期间，他师从三位知名艺术家，其中一位艺术家的作品曾在2012年创下在世艺术家拍卖的最高价纪录",
            "answer": "苏笑柏"},
        {
            "question": "一位画家，父亲心脏病去世，有一个姐姐，与妻子育有五个子女，后婚姻破裂，后经历三段感情史。后有一部文学作品基于此人撰写，这部作品叫什么？",
            "answer": "保罗.高更"},
        {
            "question": "20世纪二十年代中在上海成立的刊物成为了我国知名学生运动的先导，在此次运动中占据领导地位的高校在近百年后有一名在21世纪初某少儿电视剧中扮演重要角色的演员入学，那么请问在此电视剧中的男一号是什么时间结婚",
            "answer": "2019年4月23日"},
        {
            "question": "刘翔破纪录时候是多少岁?",
            "answer": "23岁差2天"},
        {
            "question": "有一部2010-2019年上映的电视剧a，它的一位配角在2025年春逝世，这名配角在剧中的角色是一位母亲并且帮助主角洗清冤屈。剧a男主演x曾在2010年前后出演一部中国知名古装剧，饰演重要角色，这个角色为某一政权的建立呕心沥血，也为后人所赞颂。请问该男主演x的妻子（同为演员）的家乡最知名的大学的校训？",
            "answer": "规格严格，功夫到家"},
        {
            "question": "某一改编自小说的知名电视剧a，曾激起很大反响。这部电视剧上映于21世纪的前10年，为豆瓣高分剧。女主演曾在2010-2019年出演某部抗战剧b，剧b的剧名中带有她的出生地。请问剧a男主演的祖籍是哪里",
            "answer": "宁波奉化"},
        {
            "question": "有一著名诗词人，他参加科举考试时被主考官和小试官赏识且小试官的姓是花的名字。他的出生地a的南部毗邻城市b在当前诞生了一位顶流男明星。该男星在2022年因为一部电视剧大火，并且他生于年末。求问该男星大学毕业院校成立于哪一年",
            "answer": "2004"},
        {
            "question": "某一小说家，曾获知名文学奖项。他的出生地和成长地不在一个国家。他出生的那天的50余年前，新中国一位出色的军事将领出生（即他们同月同日生）。该将军的第四任夫人和该将军的结婚日期是在哪一年的哪一月？",
            "answer": "1946.5"},
        {
            "question": "某 90 后中国男歌手， 2014 年在某档节目中翻唱了一首发表于 1979 年的歌曲，并于2025 年跨年晚会上再次与原唱同台演唱这一首歌。这首歌的名字是什么？",
            "answer": "欢颜"},
        {
            "question": "一位出生于上世纪 80 年代，毕业于北京著名音乐院校的音乐人，不仅会弹钢琴，而且还会吹小号，有自己的音乐工作室，曾前往美国学习先进的音乐制作方法和理念。与某以声音空灵悠远而著称的男歌手有过深入的合作，还曾担任多个音乐类综艺的音乐总监。这位音乐人 2025 年发布的专辑名字是什么？",
            "answer": "1981"},
    ]

    # 4. 运行研究任务
    test_case = input_data[:args.test_case_limit] if args.test_case_limit > 0 else input_data
    
    for idx, item in enumerate(test_case, 1):
        question = item['question']
        ground_truth = item['answer']
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📝 Question {idx}/{len(test_case)}: {question[:100]}...")
        logger.info(f"{'='*80}")

        # Run agent (WebWeaver / TTS / single)
        if mode == 'webweaver':
            final_result = await agent.run(question)
        elif use_tts_mode:
            final_result = await agent.run(
                question=question,
                ground_truth=ground_truth,
                num_parallel_agents=args.num_parallel_agents
            )
        else:
            final_result = await agent.run(question)

        # 5. 打印结果
        print("\n" + "="*80)
        print("📊 RESULTS")
        print("="*80)
        print(f"Q: {final_result['question']}")
        print(f"Ground Truth: {ground_truth}")
        
        if mode == 'webweaver':
            print(f"\n--- Final Outline ---")
            print(final_result.get('final_outline', ''))
            print(f"\n--- Final Report ---")
            print(final_result.get('final_report', ''))
            print(f"\nMemory Bank Size: {final_result.get('memory_bank_size', 0)}")
        elif use_tts_mode:
            print(f"Final Answer (TTS): {final_result['final_synthesized_answer']}")
            print(f"\n--- Parallel Runs: {len(final_result['parallel_runs'])} ---")
            for i, run in enumerate(final_result['parallel_runs'], 1):
                print(f"  Agent {i}: {run.get('prediction', 'N/A')[:100]}...")
        else:
            print(f"Prediction: {final_result['prediction']}")
            print(f"\n--- Report ---")
            print(final_result['report'])
        
        if args.verbose:
            print(f"\n--- Full Trajectory ---")
            if mode == 'webweaver':
                # WebWeaver returns planner/writer internals in logs; not included by default
                print("(WebWeaver) Full trajectory logging is not enabled in main.py; use CLI or examples/webweaver_usage.py for detailed logs.")
            elif use_tts_mode:
                print(json.dumps(final_result['parallel_runs'], indent=2, ensure_ascii=False))
            else:
                print(json.dumps(final_result['trajectory'], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="WebResearcher: Iterative Deep-Research Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single agent (default, cost-effective)
  python main.py --test_case_limit 1
  
  # Test-Time Scaling (3-5x cost, higher accuracy)
  python main.py --use_tts --num_parallel_agents 3 --test_case_limit 1
  
  # WebWeaver dual-agent (dynamic outline, citation-grounded report)
  python main.py --use_webweaver --test_case_limit 1
  
  # Custom model and tools
  python main.py --model gpt-4o --function_list search python
        """
    )
    
    # Model configuration
    parser.add_argument("--model", type=str, default="o3-mini",
                        help="LLM model name")
    parser.add_argument("--temperature", type=float, default=0.6,
                        help="Sampling temperature")
    parser.add_argument("--top_p", type=float, default=0.95,
                        help="Nucleus sampling threshold")
    parser.add_argument("--presence_penalty", type=float, default=1.1,
                        help="Presence penalty")
    parser.add_argument("--max_input_tokens", type=int, default=32000,
                        help="Maximum input tokens")
    parser.add_argument("--model_thinking_type", type=str, default='disabled',
                        choices=['enabled', 'disabled', 'auto'],
                        help="Model thinking mode")
    
    # Agent configuration
    parser.add_argument("--function_list", type=str, nargs='*',
                        default=["search", "google_scholar", "python"],
                        help="List of tools to enable, all tools: ['search', 'google_scholar', 'visit', 'python', 'parse_file']")
    
    # Modes
    parser.add_argument("--use_webweaver", action="store_true",
                        help="Enable WebWeaver dual-agent mode (Planner + Writer)")
    # Test-Time Scaling (TTS)
    parser.add_argument("--use_tts", action="store_true",
                        help="Enable Test-Time Scaling (3-5x cost, higher accuracy)")
    parser.add_argument("--num_parallel_agents", type=int, default=3,
                        help="Number of parallel agents for TTS mode")
    
    # Execution
    parser.add_argument("--test_case_limit", type=int, default=3,
                        help="Number of test cases to run (0 for all)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print full trajectory logs")
    
    args = parser.parse_args()
    
    # Print configuration
    logger.info("🚀 Starting WebResearcher/WebWeaver")
    logger.info(f"   Model: {args.model}")
    mode_label = 'WebWeaver' if args.use_webweaver else ('TTS (Test-Time Scaling)' if args.use_tts else 'Single Agent')
    logger.info(f"   Mode: {mode_label}")
    logger.info(f"   Tools: {', '.join(args.function_list)}")
    
    asyncio.run(main(args))
