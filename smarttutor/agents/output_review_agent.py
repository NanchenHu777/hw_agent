"""
SmartTutor - 作业辅导智能体
输出审查 Agent - 对生成的答案进行后检验
"""

from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass
from enum import Enum
import re

from agents.multi_model_client import multi_model_client


class SafetyLevel(Enum):
    """安全级别"""
    SAFE = "safe"
    CAUTION = "caution"  # 需要注意
    UNSAFE = "unsafe"  # 不安全


@dataclass
class ReviewResult:
    """审查结果"""
    is_safe: bool
    safety_level: SafetyLevel
    issues: List[str]
    suggestions: List[str]
    needs_human_review: bool
    original_response: str
    filtered_response: Optional[str] = None


class OutputReviewAgent:
    """
    输出审查 Agent
    在答案返回给用户之前进行安全检验

    检查内容：
    1. 内容安全性（无有害内容）
    2. 事实准确性（关键事实是否有明显错误）
    3. 答案质量（是否回答了问题）
    4. 年级适配性（难度是否合适）
    5. 格式规范性（数学公式是否正确）
    """

    # 有害内容关键词
    HARMFUL_PATTERNS = [
        # 暴力相关
        r"杀人", r"谋杀", r"暴力", r"虐待",
        # 违法相关
        r"犯罪", r"赌博", r"吸毒", r"走私",
        # 危险行为
        r"自杀", r"自残", r"危险.*实验",
        # 政治敏感（对于作业辅导）
        r"分裂.*国家", r"推翻.*政府",
    ]

    # 答案质量问题
    QUALITY_PATTERNS = [
        r"我不知道", r"无法回答", r"这个问题",
        r"抱歉.*无法", r"超出.*能力"
    ]

    # 需要人工审核的关键词
    HUMAN_REVIEW_PATTERNS = [
        r"争议", r"政治", r"敏感", r"宗教",
        r"可能.*不正确", r"需要.*核实",
    ]

    def __init__(self):
        self.llm_client = multi_model_client

    def review(
        self,
        response: str,
        original_question: str,
        user_grade: Optional[str] = None,
        use_llm_review: bool = True
    ) -> ReviewResult:
        """
        审查答案

        Args:
            response: 生成的答案
            original_question: 原始问题
            user_grade: 用户年级（用于检查难度适配）
            use_llm_review: 是否使用 LLM 进行深度审查

        Returns:
            ReviewResult: 审查结果
        """
        issues = []
        suggestions = []
        needs_human_review = False

        # 1. 规则基础检查
        rule_result = self._rule_based_check(response)
        issues.extend(rule_result["issues"])
        needs_human_review = needs_human_review or rule_result["needs_review"]

        # 2. 答案质量检查
        quality_result = self._quality_check(response, original_question)
        issues.extend(quality_result["issues"])
        suggestions.extend(quality_result["suggestions"])

        # 3. 格式检查
        format_result = self._format_check(response)
        issues.extend(format_result["issues"])

        # 4. 年级适配检查
        if user_grade:
            grade_result = self._grade_adapt_check(response, user_grade)
            suggestions.extend(grade_result["suggestions"])

        # 5. LLM 深度审查（可选）
        if use_llm_review and len(issues) == 0:
            llm_result = self._llm_review(response, original_question)
            if llm_result["unsafe"]:
                issues.append(f"LLM审查发现: {llm_result['reason']}")
                needs_human_review = True

        # 判断安全级别
        if any(re.search(p, response) for p in self.HARMFUL_PATTERNS):
            safety_level = SafetyLevel.UNSAFE
            is_safe = False
        elif issues:
            safety_level = SafetyLevel.CAUTION
            is_safe = True
        else:
            safety_level = SafetyLevel.SAFE
            is_safe = True

        return ReviewResult(
            is_safe=is_safe,
            safety_level=safety_level,
            issues=issues,
            suggestions=suggestions,
            needs_human_review=needs_human_review,
            original_response=response
        )

    def review_and_filter(
        self,
        response: str,
        original_question: str,
        user_grade: Optional[str] = None
    ) -> Tuple[str, ReviewResult]:
        """
        审查并过滤答案

        Returns:
            (处理后的答案, 审查结果)
        """
        result = self.review(response, original_question, user_grade)

        filtered_response = result.original_response

        # 根据审查结果过滤内容
        if result.safety_level == SafetyLevel.UNSAFE:
            filtered_response = self._generate_safe_response(original_question)
        elif result.needs_human_review:
            filtered_response = self._add_caution_note(filtered_response, result.issues)

        result.filtered_response = filtered_response
        return filtered_response, result

    def _rule_based_check(self, response: str) -> Dict[str, Any]:
        """基于规则的检查"""
        issues = []
        needs_review = False
        response_lower = response.lower()

        # 检查有害内容
        for pattern in self.HARMFUL_PATTERNS:
            if re.search(pattern, response_lower):
                issues.append(f"检测到潜在有害内容: {pattern}")

        # 检查是否需要人工审核
        for pattern in self.HUMAN_REVIEW_PATTERNS:
            if re.search(pattern, response_lower):
                needs_review = True
                issues.append(f"需要人工审核: 涉及敏感话题")

        return {
            "issues": issues,
            "needs_review": needs_review
        }

    def _quality_check(self, response: str, question: str) -> Dict[str, Any]:
        """答案质量检查"""
        issues = []
        suggestions = []

        # 检查是否包含拒绝回答的表述
        for pattern in self.QUALITY_PATTERNS:
            if re.search(pattern, response):
                issues.append(f"答案质量警告: 可能包含低质量内容")
                break

        # 检查答案长度
        if len(response) < 20:
            issues.append("答案过短，可能未完整回答问题")
        elif len(response) > 5000:
            suggestions.append("答案较长，建议分段或分步骤讲解")

        # 检查是否与问题相关
        # （这里简化，实际可能需要 LLM 判断）
        question_keywords = set(question.lower())
        response_keywords = set(response.lower())
        overlap = question_keywords & response_keywords

        if len(overlap) < 2 and len(question) > 5:
            suggestions.append("答案可能偏离问题，建议检查相关性")

        return {
            "issues": issues,
            "suggestions": suggestions
        }

    def _format_check(self, response: str) -> Dict[str, Any]:
        """格式检查"""
        issues = []

        # 检查 LaTeX 格式
        latex_patterns = [
            (r'\$[^$]+\$', '行内公式'),  # 行内公式
            (r'\$\$[^$]+\$\$', '行间公式'),  # 行间公式
        ]

        has_latex = False
        for pattern, name in latex_patterns:
            if re.search(pattern, response):
                has_latex = True
                # 检查是否正确闭合
                matches = re.findall(pattern, response)
                for match in matches:
                    # 简单检查：确保没有未闭合的 $
                    if match.count('$') % 2 != 0:
                        issues.append(f"LaTeX格式错误: {match}")

        # 检查是否有乱码或特殊字符
        if re.search(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', response):
            issues.append("检测到可能的乱码字符")

        return {
            "issues": issues
        }

    def _grade_adapt_check(self, response: str, grade: str) -> Dict[str, Any]:
        """年级适配检查"""
        suggestions = []

        # 检查是否使用了过于专业的术语
        advanced_terms = {
            "大一": ["泛函", "拓扑", "测度论"],
            "大二": ["抽象代数", "实变函数", "拓扑学"],
            "高三": ["极限", "微分", "积分"],
        }

        if grade in advanced_terms:
            terms = advanced_terms[grade]
            for term in terms:
                if term in response and grade in ["高一", "高二", "初三", "初二", "初一"]:
                    suggestions.append(f"答案可能包含超出{grade}水平的专业术语，建议简化解释")

        return {
            "suggestions": suggestions
        }

    def _llm_review(self, response: str, question: str) -> Dict[str, Any]:
        """
        使用 LLM 进行深度审查
        """
        prompt = f"""请审查以下答案是否存在问题：

原始问题: {question}

答案内容:
{response}

请检查以下方面：
1. 内容是否有错误或误导性信息
2. 是否包含不当内容
3. 是否适合学生阅读

请以JSON格式输出：
{{
  "unsafe": true/false,
  "reason": "如果unsafe为true，说明原因",
  "score": 1-10的答案质量评分
}}"""

        try:
            result = self.llm_client.structured_output(
                message="请审查答案",
                system_prompt=prompt,
                task="default",
                format_json=True
            )

            return {
                "unsafe": result.get("unsafe", False),
                "reason": result.get("reason", ""),
                "score": result.get("score", 10)
            }

        except Exception as e:
            print(f"LLM审查失败: {e}")
            return {
                "unsafe": False,
                "reason": "",
                "score": 10
            }

    def _generate_safe_response(self, question: str) -> str:
        """生成安全的替代回答"""
        return (
            "抱歉，我无法回答这个问题，因为它可能包含不适合讨论的内容。"
            "如果您有数学或历史作业问题，我很乐意帮助您。"
        )

    def _add_caution_note(self, response: str, issues: List[str]) -> str:
        """添加注意事项"""
        if not issues:
            return response

        caution_header = "\n\n---\n**⚠️ 注意事项**\n"
        issues_text = "\n".join([f"- {issue}" for issue in issues[:3]])
        caution_footer = "\n---\n"

        return response + caution_header + issues_text + caution_footer


# 全局实例
output_review_agent = OutputReviewAgent()
