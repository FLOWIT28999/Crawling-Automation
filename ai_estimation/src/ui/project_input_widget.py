#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
프로젝트 정보 입력을 위한 위젯
사용자로부터 프로젝트 정보를 입력받는 UI 컴포넌트입니다.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QSpinBox, QLabel, QGroupBox
)
from PySide6.QtCore import Signal

class ProjectInputWidget(QWidget):
    """
    프로젝트 정보 입력 위젯
    사용자로부터 프로젝트 관련 정보를 입력받는 폼을 제공합니다.
    """
    
    # 커스텀 시그널 정의
    generate_estimate_requested = Signal()
    save_estimate_requested = Signal()
    
    def __init__(self, parent=None):
        """
        위젯 초기화
        
        Args:
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """UI 컴포넌트 초기화 및 레이아웃 설정"""
        main_layout = QVBoxLayout(self)
        
        # 기본 정보 그룹
        basic_group = QGroupBox("기본 정보")
        basic_layout = QFormLayout()
        
        self.project_name = QLineEdit()
        self.project_type = QComboBox()
        self.project_type.addItems(["웹 개발", "모바일 앱", "데스크톱 앱", "기타"])
        
        self.client_name = QLineEdit()
        self.project_period = QSpinBox()
        self.project_period.setRange(1, 36)
        self.project_period.setSuffix(" 개월")
        
        # 개발 수준 선택 추가
        self.dev_level = QComboBox()
        self.dev_level.addItems([
            "기업형 (Enterprise)",
            "전문가형 (Professional)",
            "표준형 (Standard)",
            "기본형 (Basic)"
        ])
        
        basic_layout.addRow("프로젝트명:", self.project_name)
        basic_layout.addRow("프로젝트 유형:", self.project_type)
        basic_layout.addRow("클라이언트:", self.client_name)
        basic_layout.addRow("예상 기간:", self.project_period)
        basic_layout.addRow("개발 수준:", self.dev_level)
        
        basic_group.setLayout(basic_layout)
        
        # 요구사항 그룹
        req_group = QGroupBox("요구사항")
        req_layout = QVBoxLayout()
        
        self.requirements = QTextEdit()
        self.requirements.setPlaceholderText("프로젝트의 주요 요구사항을 입력하세요...")
        req_layout.addWidget(self.requirements)
        
        req_group.setLayout(req_layout)
        
        # 기술 스택 그룹
        tech_group = QGroupBox("기술 스택")
        tech_layout = QVBoxLayout()
        
        self.tech_stack = QTextEdit()
        self.tech_stack.setPlaceholderText("사용될 기술 스택을 입력하세요...")
        tech_layout.addWidget(self.tech_stack)
        
        tech_group.setLayout(tech_layout)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("견적서 생성")
        self.save_btn = QPushButton("견적서 저장")
        self.save_btn.setEnabled(False)
        
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.save_btn)
        
        # 메인 레이아웃에 추가
        main_layout.addWidget(basic_group)
        main_layout.addWidget(req_group)
        main_layout.addWidget(tech_group)
        main_layout.addLayout(button_layout)
        
        # 이벤트 연결
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        self.save_btn.clicked.connect(self._on_save_clicked)
        
    def get_project_data(self):
        """
        입력된 프로젝트 데이터를 딕셔너리 형태로 반환
        
        Returns:
            dict: 프로젝트 데이터
        """
        return {
            "project_name": self.project_name.text(),
            "project_type": self.project_type.currentText(),
            "client_name": self.client_name.text(),
            "project_period": self.project_period.value(),
            "dev_level": self.dev_level.currentText(),
            "requirements": self.requirements.toPlainText(),
            "tech_stack": self.tech_stack.toPlainText()
        }
        
    def _on_generate_clicked(self):
        """견적서 생성 버튼 클릭 이벤트 처리"""
        self.generate_estimate_requested.emit()
        self.save_btn.setEnabled(True)
        
    def _on_save_clicked(self):
        """견적서 저장 버튼 클릭 이벤트 처리"""
        self.save_estimate_requested.emit() 