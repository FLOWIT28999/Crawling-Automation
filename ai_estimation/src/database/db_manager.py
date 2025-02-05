"""
데이터베이스 관리 모듈
SQLite 데이터베이스를 사용하여 프로젝트 데이터를 관리합니다.
"""

import sqlite3
import json
import logging
from typing import Dict, Any, Optional
from src.config.constants import DB_FILE, ERROR_MESSAGES

logger = logging.getLogger(__name__)

class DatabaseManager:
    """데이터베이스 관리를 위한 클래스"""
    
    def __init__(self):
        """데이터베이스 연결 및 테이블 초기화"""
        try:
            self.conn = sqlite3.connect(DB_FILE)
            self.cursor = self.conn.cursor()
            self._create_tables()
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 초기화 중 오류 발생: {e}")
            raise Exception(ERROR_MESSAGES["DB_ERROR"])

    def _create_tables(self) -> None:
        """필요한 테이블들을 생성합니다."""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data JSON
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"테이블 생성 중 오류 발생: {e}")
            raise Exception(ERROR_MESSAGES["DB_ERROR"])

    def save_project(self, name: str, data: Dict[str, Any]) -> int:
        """새로운 프로젝트를 저장합니다."""
        try:
            self.cursor.execute(
                'INSERT INTO projects (name, data) VALUES (?, ?)',
                (name, json.dumps(data, ensure_ascii=False))
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"프로젝트 저장 중 오류 발생: {e}")
            raise Exception(ERROR_MESSAGES["DB_ERROR"])

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """프로젝트 정보를 조회합니다."""
        try:
            self.cursor.execute(
                'SELECT name, data FROM projects WHERE id = ?',
                (project_id,)
            )
            result = self.cursor.fetchone()
            if result:
                return {
                    'name': result[0],
                    'data': json.loads(result[1])
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"프로젝트 조회 중 오류 발생: {e}")
            raise Exception(ERROR_MESSAGES["DB_ERROR"])

    def update_project(self, project_id: int, data: Dict[str, Any]) -> bool:
        """프로젝트 정보를 업데이트합니다."""
        try:
            self.cursor.execute(
                '''UPDATE projects 
                   SET data = ?, 
                       updated_at = CURRENT_TIMESTAMP 
                   WHERE id = ?''',
                (json.dumps(data, ensure_ascii=False), project_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"프로젝트 업데이트 중 오류 발생: {e}")
            raise Exception(ERROR_MESSAGES["DB_ERROR"])

    def delete_project(self, project_id: int) -> bool:
        """프로젝트를 삭제합니다."""
        try:
            self.cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"프로젝트 삭제 중 오류 발생: {e}")
            raise Exception(ERROR_MESSAGES["DB_ERROR"])

    def get_all_projects(self) -> list:
        """모든 프로젝트 목록을 조회합니다."""
        try:
            self.cursor.execute(
                'SELECT id, name, created_at FROM projects ORDER BY created_at DESC'
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"프로젝트 목록 조회 중 오류 발생: {e}")
            raise Exception(ERROR_MESSAGES["DB_ERROR"])

    def __del__(self):
        """소멸자: 데이터베이스 연결을 종료합니다."""
        try:
            self.conn.close()
        except:
            pass 