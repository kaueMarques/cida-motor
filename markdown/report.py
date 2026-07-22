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
                  dict_included, tokens_dict, accepted_transforms, rejected_transforms, 
                  semantic_status, execution_time):
        
        ganho_abs = tokens_orig - tokens_new
        ganho_pct = (ganho_abs / tokens_orig * 100.0) if tokens_orig > 0 else 0.0
        
        entry = {
            "arquivo": filepath,
            "perfil": profile,
            "tokens_originais": tokens_orig,
            "tokens_baseline": tokens_base,
            "tokens_novos": tokens_new,
            "ganho_absoluto": ganho_abs,
            "ganho_percentual_medido": ganho_pct,
            "dicionário_incluído": dict_included,
            "tokens_do_dicionario": tokens_dict,
            "transformações_aceitas": accepted_transforms,
            "transformações_rejeitadas": rejected_transforms,
            "status_semântico": semantic_status,
            "tempo_de_execução": execution_time
        }
        self.entries.append(entry)

    def generate_markdown(self):
        md = []
        md.append("# Relatório de Benchmark - CIDA Motor\n")
        md.append("| Arquivo | Perfil | Tokens Originais | Tokens Baseline | Tokens Novos | Ganho Absoluto | Ganho % | Dic. Incluído | Tokens Dic. | Status Semântico | Tempo (s) |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for e in self.entries:
            name = os.path.basename(e["arquivo"])
            md.append(f"| {name} | {e['perfil']} | {e['tokens_originais']} | {e['tokens_baseline']} | {e['tokens_novos']} | {e['ganho_absoluto']} | {e['ganho_percentual_medido']:.2f}% | {'Sim' if e['dicionário_incluído'] else 'Não'} | {e['tokens_do_dicionario']} | {e['status_semântico']} | {e['tempo_de_execução']:.4f} |")
        return "\n".join(md)

    def save_reports(self, text_path, json_path):
        os.makedirs(os.path.dirname(os.path.abspath(text_path)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
        
        md_content = self.generate_markdown()
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.entries, f, indent=4, ensure_ascii=False)
