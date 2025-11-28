"""
Report Generator Service (Agent 5: Audit Assembler)
Builds human-readable audit reports
"""
import json
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from loguru import logger

from app.database import db


class ReportGenerator:
    """
    Agent 5: Audit Assembler
    
    Builds professional audit reports from compliance results
    """
    
    async def build_report_outline(
        self,
        case_id: UUID,
        scan_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Build report outline and structure
        
        Args:
            case_id: Audit case UUID
            scan_ids: List of compliance scan IDs
            
        Returns:
            Report outline with sections
        """
        logger.info(f"Building report outline for case {case_id}")
        
        # Collect scan results
        scan_results = await self._collect_scan_results(scan_ids)
        
        # Analyze coverage
        coverage = await self._analyze_coverage(case_id, scan_results)
        
        # Build outline
        outline = {
            "sections": [
                {
                    "title": "Executive Summary",
                    "type": "summary",
                    "content": await self._generate_executive_summary(scan_results)
                },
                {
                    "title": "Compliance Overview",
                    "type": "overview",
                    "content": coverage
                },
                {
                    "title": "Detailed Findings",
                    "type": "findings",
                    "content": await self._organize_findings(scan_results)
                },
                {
                    "title": "Recommendations",
                    "type": "recommendations",
                    "content": await self._generate_recommendations(scan_results)
                }
            ],
            "coverage_summary": coverage,
            "metadata": {
                "case_id": str(case_id),
                "generated_at": datetime.utcnow().isoformat(),
                "total_scans": len(scan_ids)
            }
        }
        
        return outline
    
    async def generate_html_report(self, case_id: UUID) -> str:
        """
        Generate HTML report
        
        Args:
            case_id: Audit case UUID
            
        Returns:
            HTML report content
        """
        logger.info(f"Generating HTML report for case {case_id}")
        
        # Get case data
        async with db.acquire() as conn:
            case = await conn.fetchrow("""
                SELECT * FROM audit_cases WHERE case_id = $1
            """, case_id)
            
            if not case:
                raise ValueError(f"Case {case_id} not found")
            
            case_data = dict(case)
        
        # Get report outline
        report_data = case_data.get("report_data")
        if isinstance(report_data, str):
            report_data = json.loads(report_data)
        
        # Build HTML
        html = self._build_html_template(case_data, report_data)
        
        return html
    
    async def _collect_scan_results(self, scan_ids: List[str]) -> List[Dict[str, Any]]:
        """Collect all scan results"""
        results = []
        
        async with db.acquire() as conn:
            for scan_id in scan_ids:
                try:
                    scan_uuid = UUID(scan_id)
                    scan = await conn.fetchrow("""
                        SELECT * FROM compliance_scans WHERE scan_id = $1
                    """, scan_uuid)
                    
                    if scan:
                        scan_dict = dict(scan)
                        # Parse JSON fields
                        for field in ['final_verdict', 'investigation_result', 'matched_files']:
                            if scan_dict.get(field):
                                if isinstance(scan_dict[field], str):
                                    scan_dict[field] = json.loads(scan_dict[field])
                        results.append(scan_dict)
                except Exception as e:
                    logger.warning(f"Failed to load scan {scan_id}: {e}")
        
        return results
    
    async def _analyze_coverage(
        self,
        case_id: UUID,
        scan_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze rule coverage"""
        total_rules = len(scan_results)
        
        verdicts = [
            s.get("final_verdict", {}).get("final_verdict", "unknown")
            for s in scan_results
        ]
        
        compliant = verdicts.count("compliant")
        non_compliant = verdicts.count("non_compliant")
        partial = verdicts.count("partial")
        
        return {
            "total_rules_checked": total_rules,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "partial": partial,
            "compliance_rate": (compliant / total_rules * 100) if total_rules > 0 else 0
        }
    
    async def _generate_executive_summary(
        self,
        scan_results: List[Dict[str, Any]]
    ) -> str:
        """Generate executive summary"""
        total = len(scan_results)
        verdicts = [
            s.get("final_verdict", {}).get("final_verdict", "unknown")
            for s in scan_results
        ]
        
        compliant = verdicts.count("compliant")
        non_compliant = verdicts.count("non_compliant")
        
        summary = f"""
This compliance audit assessed {total} regulatory requirements.

Results:
- Compliant: {compliant} ({compliant/total*100:.1f}%)
- Non-Compliant: {non_compliant} ({non_compliant/total*100:.1f}%)
- Partial Compliance: {verdicts.count("partial")}

{f"Critical issues require immediate attention." if non_compliant > 0 else "No critical compliance gaps identified."}
"""
        return summary.strip()
    
    async def _organize_findings(
        self,
        scan_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Organize findings by severity"""
        findings = []
        
        for scan in scan_results:
            verdict = scan.get("final_verdict", {})
            investigation = scan.get("investigation_result", {})
            
            if verdict.get("final_verdict") in ["non_compliant", "partial"]:
                findings.append({
                    "regulation": scan.get("regulation_id", "Unknown"),
                    "verdict": verdict.get("final_verdict"),
                    "reason": verdict.get("reason", ""),
                    "evidence_count": verdict.get("evidence_count", 0),
                    "confidence": verdict.get("confidence", 0.0)
                })
        
        # Sort by severity (non_compliant first)
        findings.sort(key=lambda x: 0 if x["verdict"] == "non_compliant" else 1)
        
        return findings
    
    async def _generate_recommendations(
        self,
        scan_results: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate remediation recommendations"""
        recommendations = []
        
        for scan in scan_results:
            verdict = scan.get("final_verdict", {})
            
            if verdict.get("final_verdict") == "non_compliant":
                reason = verdict.get("reason", "")
                recommendations.append(f"Address: {reason}")
        
        if not recommendations:
            recommendations.append("Maintain current compliance posture")
        
        return recommendations[:10]  # Top 10
    
    def _build_html_template(
        self,
        case_data: Dict[str, Any],
        report_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build HTML report from template"""
        sections = report_data.get("sections", []) if report_data else []
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Compliance Audit Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .summary {{ background: #ecf0f1; padding: 20px; border-radius: 5px; }}
        .finding {{ border-left: 3px solid #e74c3c; padding: 10px; margin: 10px 0; }}
        .compliant {{ border-left-color: #27ae60; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #34495e; color: white; }}
    </style>
</head>
<body>
    <h1>Compliance Audit Report</h1>
    <p><strong>Case ID:</strong> {case_data.get('case_id')}</p>
    <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
"""
        
        # Add sections
        for section in sections:
            html += f"\n    <h2>{section['title']}</h2>\n"
            
            if section['type'] == 'summary':
                html += f'    <div class="summary">{section["content"]}</div>\n'
            
            elif section['type'] == 'findings':
                findings = section['content']
                if findings:
                    html += '    <table>\n'
                    html += '        <tr><th>Regulation</th><th>Verdict</th><th>Details</th></tr>\n'
                    for finding in findings:
                        html += f"""        <tr>
            <td>{finding['regulation']}</td>
            <td>{finding['verdict']}</td>
            <td>{finding['reason']}</td>
        </tr>\n"""
                    html += '    </table>\n'
            
            elif section['type'] == 'recommendations':
                recs = section['content']
                if recs:
                    html += '    <ul>\n'
                    for rec in recs:
                        html += f'        <li>{rec}</li>\n'
                    html += '    </ul>\n'
        
        html += """
</body>
</html>
"""
        return html


# Global service instance
report_generator = ReportGenerator()


# Convenience functions for orchestrator
async def build_report_outline(case_id: UUID, scan_ids: List[str]) -> Dict[str, Any]:
    return await report_generator.build_report_outline(case_id, scan_ids)


async def generate_html_report(case_id: UUID) -> str:
    return await report_generator.generate_html_report(case_id)
