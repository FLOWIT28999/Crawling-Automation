#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI 자동 견적 시스템의 메인 윈도우 UI 클래스
PySide6를 사용하여 구현된 메인 윈도우 인터페이스입니다.
"""

import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStatusBar, QMessageBox,
    QProgressDialog, QFileDialog
)
from PySide6.QtCore import Qt, QTimer

from .project_input_widget import ProjectInputWidget
from .estimate_view_widget import EstimateViewWidget
from core.estimate_generator import EstimateGenerator

class MainWindow(QMainWindow):
    """
    애플리케이션의 메인 윈도우 클래스
    전체 UI 레이아웃과 주요 기능을 관리합니다.
    """
    
    def __init__(self, settings, parent=None):
        """
        메인 윈도우 초기화
        
        Args:
            settings (dict): 애플리케이션 설정
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.estimate_generator = EstimateGenerator(settings)
        
        self._init_ui()
        
    def _init_ui(self):
        """UI 컴포넌트 초기화 및 레이아웃 설정"""
        self.setWindowTitle("AI 자동 견적 시스템")
        self.setMinimumSize(1200, 800)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout(central_widget)
        
        # 좌측 패널 (프로젝트 정보 입력)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.project_input = ProjectInputWidget()
        left_layout.addWidget(self.project_input)
        
        # 우측 패널 (견적서 미리보기)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.estimate_view = EstimateViewWidget()
        right_layout.addWidget(self.estimate_view)
        
        # 패널 추가
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # 상태바 설정
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 이벤트 연결
        self.project_input.generate_estimate_requested.connect(self._generate_estimate)
        self.project_input.save_estimate_requested.connect(self._save_estimate)
        
        # 로딩 다이얼로그 초기화
        self.progress_dialog = QProgressDialog(self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setWindowTitle("처리 중")
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setRange(0, 0)  # 무한 로딩 모드
        self.progress_dialog.setMinimumDuration(500)  # 0.5초 이상 걸릴 때만 표시
        
    def _generate_estimate(self):
        """견적서 생성 요청 처리"""
        try:
            project_data = self.project_input.get_project_data()
            
            # 로딩 다이얼로그 표시
            self.progress_dialog.setLabelText("견적서를 생성하는 중...")
            self.progress_dialog.show()
            
            self.status_bar.showMessage("견적서를 생성하는 중...")
            
            # AI 견적 생성 (비동기로 처리하면 더 좋을 것 같습니다)
            estimate_data = self.estimate_generator.generate(project_data)
            self.estimate_view.update_estimate(estimate_data)
            
            self.status_bar.showMessage("견적서가 생성되었습니다.", 3000)
            
        except Exception as e:
            self.logger.error(f"견적서 생성 중 오류 발생: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "오류", "견적서 생성 중 오류가 발생했습니다.")
            self.status_bar.showMessage("견적서 생성 실패", 3000)
        finally:
            self.progress_dialog.hide()
            
    def _save_estimate(self):
        """견적서 저장 요청 처리"""
        try:
            # 파일 저장 다이얼로그 표시
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "견적서 저장",
                "",
                "Excel 파일 (*.xlsx);;모든 파일 (*.*)"
            )
            
            if file_path:
                # 로딩 다이얼로그 표시
                self.progress_dialog.setLabelText("견적서를 저장하는 중...")
                self.progress_dialog.show()
                
                estimate_data = self.estimate_view.get_estimate_data()
                self.estimate_generator.save_to_excel(estimate_data, file_path)
                self.status_bar.showMessage("견적서가 저장되었습니다.", 3000)
            
        except Exception as e:
            self.logger.error(f"견적서 저장 중 오류 발생: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "오류", "견적서 저장 중 오류가 발생했습니다.")
            self.status_bar.showMessage("견적서 저장 실패", 3000)
        finally:
            self.progress_dialog.hide() 