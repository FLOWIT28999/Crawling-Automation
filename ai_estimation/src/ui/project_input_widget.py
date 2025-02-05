"""
프로젝트 정보 입력 위젯 모듈
사용자로부터 프로젝트 정보를 입력받는 UI를 구현합니다.
"""

import logging
from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QSpinBox, QPushButton,
    QScrollArea
)
from PySide6.QtCore import Qt
from src.config.constants import ERROR_MESSAGES

logger = logging.getLogger(__name__)

class RequirementWidget(QWidget):
    """요구사항 입력을 위한 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 요구사항 입력 필드
        self.requirement_edit = QLineEdit()
        self.requirement_edit.setPlaceholderText("요구사항을 입력하세요")
        layout.addWidget(self.requirement_edit)
        
        # 삭제 버튼
        delete_button = QPushButton("삭제")
        delete_button.clicked.connect(self.deleteLater)
        layout.addWidget(delete_button)
        
    def get_requirement(self) -> str:
        """입력된 요구사항을 반환합니다."""
        return self.requirement_edit.text().strip()

class ProjectInputWidget(QWidget):
    """프로젝트 정보 입력 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        
        # 스크롤 영역 생성
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 스크롤 내부 위젯
        scroll_content = QWidget()
        self.form_layout = QVBoxLayout(scroll_content)
        
        # 프로젝트명
        name_layout = QHBoxLayout()
        name_label = QLabel("프로젝트명:")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("프로젝트명을 입력하세요")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        self.form_layout.addLayout(name_layout)
        
        # 프로젝트 설명
        desc_layout = QVBoxLayout()
        desc_label = QLabel("프로젝트 설명:")
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("프로젝트에 대한 상세 설명을 입력하세요")
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)
        self.form_layout.addLayout(desc_layout)
        
        # 요구사항
        req_layout = QVBoxLayout()
        req_header = QHBoxLayout()
        req_label = QLabel("요구사항:")
        add_req_button = QPushButton("추가")
        add_req_button.clicked.connect(self._add_requirement)
        req_header.addWidget(req_label)
        req_header.addWidget(add_req_button)
        req_layout.addLayout(req_header)
        
        # 요구사항 목록을 담을 컨테이너
        self.requirements_container = QWidget()
        self.requirements_layout = QVBoxLayout(self.requirements_container)
        self.requirements_layout.setContentsMargins(0, 0, 0, 0)
        req_layout.addWidget(self.requirements_container)
        
        self.form_layout.addLayout(req_layout)
        
        # 예상 기간
        duration_layout = QHBoxLayout()
        duration_label = QLabel("예상 기간(월):")
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 60)
        self.duration_spin.setValue(3)
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_spin)
        self.form_layout.addLayout(duration_layout)
        
        # 팀 규모
        team_layout = QHBoxLayout()
        team_label = QLabel("팀 규모(명):")
        self.team_spin = QSpinBox()
        self.team_spin.setRange(1, 100)
        self.team_spin.setValue(3)
        team_layout.addWidget(team_label)
        team_layout.addWidget(self.team_spin)
        self.form_layout.addLayout(team_layout)
        
        # 여백 추가
        self.form_layout.addStretch()
        
        # 스크롤 영역에 위젯 설정
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # 초기 요구사항 항목 추가
        self._add_requirement()
        
    def _add_requirement(self):
        """새로운 요구사항 입력 필드를 추가합니다."""
        requirement = RequirementWidget()
        self.requirements_layout.addWidget(requirement)
        
    def get_project_info(self) -> Dict[str, Any]:
        """입력된 프로젝트 정보를 반환합니다."""
        try:
            # 기본 정보 수집
            name = self.name_edit.text().strip()
            if not name:
                raise ValueError("프로젝트명을 입력해주세요.")
                
            # 요구사항 수집
            requirements = []
            for i in range(self.requirements_layout.count()):
                widget = self.requirements_layout.itemAt(i).widget()
                if isinstance(widget, RequirementWidget):
                    req = widget.get_requirement()
                    if req:
                        requirements.append(req)
                        
            if not requirements:
                raise ValueError("최소 하나 이상의 요구사항을 입력해주세요.")
                
            return {
                'name': name,
                'description': self.desc_edit.toPlainText().strip(),
                'requirements': requirements,
                'duration': self.duration_spin.value(),
                'team_size': self.team_spin.value()
            }
            
        except Exception as e:
            logger.error(f"프로젝트 정보 수집 중 오류 발생: {e}")
            raise Exception(str(e))
            
    def clear(self):
        """입력 필드를 초기화합니다."""
        self.name_edit.clear()
        self.desc_edit.clear()
        
        # 요구사항 필드 초기화
        while self.requirements_layout.count():
            item = self.requirements_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self.duration_spin.setValue(3)
        self.team_spin.setValue(3)
        
        # 새로운 요구사항 필드 추가
        self._add_requirement() 