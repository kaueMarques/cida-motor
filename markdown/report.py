import json
import os

class ReportGenerator:
    """
    Collects performance and compression metrics for each processed file
    and outputs reports in Markdown and JSON.
    """
    def __init__(self):
        self.entries = []

    def add_entry(self, filepath, profile, tokens_orig, tokens_base, tokens_new, 
                  dict_included, tokens_sidecar, tokens_aux, accepted_transforms, rejected_transforms, 
                  semantic_status, execution_time):
        
        tokens_originais = tokens_orig
        tokens_minificados = tokens_new
        
        economia_bruta = tokens_originais - tokens_minificados
        overhead_total = tokens_sidecar + tokens_aux
        economia_liquida = economia_bruta - overhead_total
        economia_liquida_percentual = (economia_liquida / tokens_originais * 100.0) if tokens_originais > 0 else 0.0
        
        ganho_abs = tokens_originais - tokens_minificados
        ganho_pct = (ganho_abs / tokens_originais * 100.0) if tokens_originais > 0 else 0.0
        
        entry = {
            "arquivo": filepath,
            "perfil": profile,
            "tokens_originais": tokens_originais,
            "tokens_baseline": tokens_base,
            "tokens_novos": tokens_minificados,
            "tokens_minificados": tokens_minificados,
            "tokens_sidecar": tokens_sidecar,
            "tokens_auxiliares": tokens_aux,
            "overhead_total": overhead_total,
            "economia_bruta": economia_bruta,
            "economia_liquida": economia_liquida,
            "economia_liquida_percentual": economia_liquida_percentual,
            "ganho_absoluto": ganho_abs,
            "ganho_percentual_medido": ganho_pct,
            "ganho_liquido_absoluto": economia_liquida,
            "ganho_liquido_percentual": economia_liquida_percentual,
            "dicionário_incluído": dict_included,
            "transformações_aceitas": accepted_transforms,
            "transformações_rejeitadas": rejected_transforms,
            "status_semântico": semantic_status,
            "tempo_de_execução": execution_time
        }
        self.entries.append(entry)

    def make_deterministic(self, src_abs):
        for e in self.entries:
            # Resolve relative path using forward slashes for platform consistency
            rel = os.path.relpath(e["arquivo"], src_abs).replace('\\', '/')
            e["arquivo"] = rel
            e["tempo_de_execução"] = 0.0

    def generate_markdown(self, deterministic=False):
        md = []
        md.append("# Relatório de Benchmark - CIDA Motor\n")
        md.append("| Arquivo | Perfil | Tokens Originais | Tokens Baseline | Tokens Minificados | Tokens Sidecar | Tokens Aux | Overhead Total | Economia Bruta | Economia Líquida | Economia Líquida % | Status Semântico | Tempo (s) |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for e in self.entries:
            name = e["arquivo"] if deterministic else os.path.basename(e["arquivo"])
            tempo = 0.0 if deterministic else e["tempo_de_execução"]
            md.append(f"| {name} | {e['perfil']} | {e['tokens_originais']} | {e['tokens_baseline']} | {e['tokens_minificados']} | {e['tokens_sidecar']} | {e['tokens_auxiliares']} | {e['overhead_total']} | {e['economia_bruta']} | {e['economia_liquida']} | {e['economia_liquida_percentual']:.2f}% | {e['status_semântico']} | {tempo:.4f} |")
        return "\n".join(md)

    def save_reports(self, text_path, json_path, src_abs, report_format="both"):
        import re
        self.make_deterministic(src_abs)
        
        # Regex check for absolute path leakage
        abs_patterns = [r'[A-Za-z]:[\\/]', r'/home/', r'/Users/', r'/tmp/', r'IdeaProjects']
        
        for e in self.entries:
            path = e["arquivo"]
            for pat in abs_patterns:
                if re.search(pat, path):
                    raise ValueError(f"Absolute path found in report entry: {path}")
                    
        md_content = self.generate_markdown(deterministic=True)
        for pat in abs_patterns:
            if re.search(pat, md_content):
                raise ValueError("Absolute path found in generated markdown report")
                
        # Write only requested report formats
        if report_format in ["text", "both"]:
            os.makedirs(os.path.dirname(os.path.abspath(text_path)), exist_ok=True)
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
                
        if report_format in ["json", "both"]:
            os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.entries, f, indent=4, ensure_ascii=False)

