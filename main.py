# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
"""
import argparse
import asyncio
import json
from loguru import logger
from dotenv import load_dotenv

load_dotenv('.env', override=True)
from webresearcher.react_agent import MultiTurnReactAgent


async def main(args):
    # 1. 定义你的 LLM 配置
    llm_config = {
        "model": args.model,
        "generate_cfg": {
            'max_input_tokens': args.max_input_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "presence_penalty": args.presence_penalty,
            "model_thinking_type": args.model_thinking_type,
        }
    }

    # 2. 实例化 WebResearcherAgent
    agent = MultiTurnReactAgent(
        llm_config=llm_config,
        function_list=args.function_list,
        # function_list=["search", "visit", "google_scholar", "PythonInterpreter"]
    )

    # 3. 准备输入数据 (与原始的 `run` 格式一致)
    input_data = [
        {
            "question": "刘翔破纪录时候是多少岁?",
            "answer": "23岁差2天"},
        {
            "question": "20世纪二十年代中在上海成立的刊物成为了我国知名学生运动的先导，在此次运动中占据领导地位的高校在近百年后有一名在21世纪初某少儿电视剧中扮演重要角色的演员入学，那么请问在此电视剧中的男一号是什么时间结婚",
            "answer": "2019年4月23日"},
        {
            "question": "请根据以下线索找出这位艺术家的姓名：曾在中国中央美术学院及德国杜塞尔多夫艺术学院深造，并赴德国留学。在德国学习期间，他师从三位知名艺术家，其中一位艺术家的作品曾在2012年创下在世艺术家拍卖的最高价纪录",
            "answer": "苏笑柏"},
        {
            "question": "一位画家，父亲心脏病去世，有一个姐姐，与妻子育有五个子女，后婚姻破裂，后经历三段感情史。后有一部文学作品基于此人撰写，这部作品叫什么？",
            "answer": "保罗.高更"},
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

    # 4. 运行完整的并行研究与总结
    test_case = input_data[:args.test_case_limit] if args.test_case_limit > 0 else input_data
    for i in test_case:
        question = i['question']
        logger.info(f"Processing question: {question}")

        final_result = await agent.run(question)

        # 5. 打印结果
        logger.info(f"final_result: {final_result}")
        print("\n\n--- 最终研究结果 ---")
        print(f"Q: {final_result['question']}")
        print(f"A (Ground Truth): {i['answer']}")
        print(f"A (prediction): {final_result['prediction']}")
        print("\n--- 报告 ---")
        print(f"{final_result['report']}")
        print("\n--- 日志 ---")
        print(json.dumps(final_result['trajectory'], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="o3-mini")
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--presence_penalty", type=float, default=1.1)
    parser.add_argument("--max_input_tokens", type=int, default=32000)
    parser.add_argument("--model_thinking_type", type=str, default='enabled')
    # function_list=["search", "visit", "google_scholar", "PythonInterpreter"]
    parser.add_argument("--function_list", type=str, nargs='*',
                        default=["search", "google_scholar", "PythonInterpreter"])
    parser.add_argument("--test_case_limit", type=int, default=3)
    args = parser.parse_args()
    print(args)

    asyncio.run(main(args))
