#!/usr/bin/env python3
"""
RISS 학술논문 자동 수집 시스템
메인 실행 파일
"""

import sys
import os
import logging
import argparse
import asyncio
from pathlib import Path
from typing import List

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.backend import PaperCollectionEngine
from gui import main as gui_main


def setup_logging(verbose: bool = False):
    """로깅 설정"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 로그 파일명
    from datetime import datetime
    log_file = log_dir / f"riss_automation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 로깅 설정
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Playwright 로그 레벨 조정
    logging.getLogger('playwright').setLevel(logging.WARNING)
    
    return log_file


async def run_cli(args):
    """CLI 모드 실행"""
    print("=" * 50)
    print("RISS 학술논문 자동 수집 시스템 (CLI 모드)")
    print("=" * 50)
    
    # 설정 로드
    config = {
        'search_keywords': args.keywords.split(','),
        'max_papers': args.count,
        'free_papers_only': args.free_only,
        'output_path': args.output,
        'gemini_api_key': args.api_key or os.getenv('GEMINI_API_KEY', '')
    }
    
    # 엔진 생성
    engine = PaperCollectionEngine(config)
    
    # 진행 상황 콜백
    def print_progress(value):
        print(f"\r진행률: {value}%", end='', flush=True)
        
    def print_status(message):
        print(f"\n상태: {message}")
        
    engine.set_progress_callback(print_progress)
    engine.set_status_callback(print_status)
    
    # 논문 수집
    print(f"\n검색 키워드: {', '.join(config['search_keywords'])}")
    print(f"목표 논문 수: {config['max_papers']}")
    print(f"무료 논문만: {'예' if config['free_papers_only'] else '아니오'}")
    print("\n수집을 시작합니다...\n")
    
    result = await engine.collect_papers_async(
        config['search_keywords'],
        config['max_papers']
    )
    
    print("\n" + "=" * 50)
    
    if result['success']:
        print(f"✅ 수집 성공!")
        print(f"- 수집된 논문: {len(result['papers'])}개")
        
        if result.get('files'):
            print("\n생성된 파일:")
            for file_type, filepath in result['files'].items():
                print(f"  - {file_type.upper()}: {filepath}")
                
        if result.get('statistics'):
            stats = result['statistics']
            print(f"\n통계:")
            print(f"  - 초록 있는 논문: {stats.get('has_abstract', 0)}개")
            print(f"  - 원문 링크 있는 논문: {stats.get('has_fulltext', 0)}개")
            
    else:
        print(f"❌ 수집 실패: {result.get('error', '알 수 없는 오류')}")
        
    print("=" * 50)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='RISS 학술논문 자동 수집 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # GUI 모드 실행
  python run.py
  
  # CLI 모드로 AI 논문 10개 수집
  python run.py --cli -k "AI,머신러닝" -c 10
  
  # Gemini API 키 지정하여 실행
  python run.py --cli -k "딥러닝" --api-key YOUR_API_KEY
  
  # 특정 경로에 저장
  python run.py --cli -k "자연어처리" -o ./my_results
        """
    )
    
    # 기본 옵션
    parser.add_argument(
        '--cli',
        action='store_true',
        help='CLI 모드로 실행 (GUI 없이)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='상세 로그 출력'
    )
    
    # CLI 모드 옵션
    cli_group = parser.add_argument_group('CLI 모드 옵션')
    
    cli_group.add_argument(
        '-k', '--keywords',
        type=str,
        help='검색 키워드 (쉼표로 구분)'
    )
    
    cli_group.add_argument(
        '-c', '--count',
        type=int,
        default=50,
        help='수집할 논문 개수 (기본값: 50)'
    )
    
    cli_group.add_argument(
        '--free-only',
        action='store_true',
        default=True,
        help='무료 논문만 수집 (기본값: True)'
    )
    
    cli_group.add_argument(
        '-o', '--output',
        type=str,
        default='./results',
        help='출력 경로 (기본값: ./results)'
    )
    
    cli_group.add_argument(
        '--api-key',
        type=str,
        help='Gemini API 키'
    )
    
    args = parser.parse_args()
    
    # 로깅 설정
    log_file = setup_logging(args.verbose)
    logging.info(f"로그 파일: {log_file}")
    
    try:
        if args.cli:
            # CLI 모드
            if not args.keywords:
                parser.error("CLI 모드에서는 -k/--keywords 옵션이 필요합니다")
                
            # Playwright 설치 확인
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    # 브라우저 설치 확인
                    try:
                        browser = p.chromium.launch(headless=True)
                        browser.close()
                    except:
                        print("Playwright 브라우저를 설치합니다...")
                        os.system("playwright install chromium")
            except ImportError:
                print("Playwright가 설치되어 있지 않습니다.")
                print("다음 명령어로 설치해주세요:")
                print("  pip install playwright")
                print("  playwright install chromium")
                sys.exit(1)
                
            # CLI 모드 실행
            asyncio.run(run_cli(args))
        else:
            # GUI 모드
            logging.info("GUI 모드로 시작합니다")
            gui_main()
            
    except KeyboardInterrupt:
        print("\n\n프로그램이 사용자에 의해 중단되었습니다.")
        logging.info("프로그램 중단됨")
    except Exception as e:
        logging.error(f"예상치 못한 오류: {e}", exc_info=True)
        print(f"\n오류가 발생했습니다: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()