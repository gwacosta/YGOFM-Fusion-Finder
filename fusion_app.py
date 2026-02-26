import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
import sys
import os


class YugiohFusionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yu-Gi-Oh Forbidden Memories - Fusion Finder")
        self.root.geometry("900x700")
        
        # Dicionários para armazenar os dados
        self.card_fusions = {}  # {card_name: [(card2, result, atk, def), ...]}
        self.general_fusions = []  # [(type1, type2, result, atk, def), ...]
        self.card_stats = {}  # {card_name: (atk, def)}
        self.fusion_results = {}  # {result_name: [(card1, card2, ...), ...]} - mapa reverso
        
        # Tipos válidos de monstros do Yu-Gi-Oh
        self.valid_monster_types = [
            'Aqua', 'Beast', 'Beast-Warrior', 'Dinosaur', 'Dragon', 'Fairy', 
            'Fiend', 'Fish', 'Insect', 'Machine', 'Plant', 'Pyro', 'Reptile', 
            'Rock', 'Spellcaster', 'Thunder', 'Warrior', 'Winged Beast', 
            'WingedBeast', 'Zombie'
        ]
        
        # Carregar dados
        self.load_fusions()
        
        # Criar interface
        self.create_widgets()
    
    def load_fusions(self):
        """Carrega as fusões do arquivo fusions.txt"""
        try:
            # Determinar o caminho correto do arquivo
            if getattr(sys, 'frozen', False):
                # Se estiver rodando como executável
                base_path = sys._MEIPASS
            else:
                # Se estiver rodando como script Python
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            fusions_path = os.path.join(base_path, 'fusions.txt')
            
            with open(fusions_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extrair fusões gerais (com [Type])
            self.extract_general_fusions(content)
            
            # Extrair fusões específicas de cartas
            self.extract_card_fusions(content)
            
            # Criar mapa reverso de resultados
            self.build_fusion_results_map()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar fusions.txt: {str(e)}")
    
    def extract_general_fusions(self, content):
        """Extrai fusões gerais do tipo [Type1] + [Type2] = Result"""
        # Padrão para fusões gerais com [colchetes]
        pattern = r'\[([^\]]+)\]\s*\+\s*\[([^\]]+)\]\s*=\s*([^\(]+)\s*\((\d+)/(\d+)\)'
        matches = re.findall(pattern, content)
        
        for match in matches:
            type1, type2, result, atk, defense = match
            self.general_fusions.append({
                'type1': type1.strip(),
                'type2': type2.strip(),
                'result': result.strip(),
                'atk': atk.strip(),
                'def': defense.strip(),
                'req1': '',
                'req2': ''
            })
        
        # Padrão alternativo com múltiplos resultados
        pattern2 = r'\[([^\]]+)\]\s*\+\s*([^\[=]+?)\s*=\s*([^\(]+)\s*\((\d+)/(\d+)\)'
        matches2 = re.findall(pattern2, content)
        
        for match in matches2:
            type1, card_or_type, result, atk, defense = match
            if not card_or_type.strip().startswith('['):
                self.general_fusions.append({
                    'type1': type1.strip(),
                    'type2': card_or_type.strip(),
                    'result': result.strip(),
                    'atk': atk.strip(),
                    'def': defense.strip(),
                    'req1': '',
                    'req2': ''
                })
        
        # Padrão para fusões com requisitos (ex: Beast (<1300) + Warrior (<1300) = Tiger Axe)
        pattern3 = r'([A-Za-z\s]+?)\s*(\([^)]+\))?\s*\+\s*([A-Za-z\s]+?)\s*(\([^)]+\))?\s*=\s*([^\(\r\n]+?)(?:\s*\((\d+)/(\d+)\))?$'
        
        # Procurar na seção de fusões do Kingtut1
        kingtut_section = re.search(r'\*\*\* Below is Kingtut1\'s General Fusions.*?(?=\n={20,}|\Z)', content, re.DOTALL)
        if kingtut_section:
            lines = kingtut_section.group(0).split('\n')
            for line in lines:
                line = line.strip()
                if '+' in line and '=' in line and not line.startswith('***'):
                    # Tentar extrair fusão com requisitos
                    match = re.match(r'([A-Za-z\s]+?)\s*(\([^)]+\))?\s*\+\s*([A-Za-z\s]+?)\s*(\([^)]+\))?\s*=\s*([^\(]+?)(?:\s*\((\d+)/(\d+)\))?$', line)
                    if match:
                        type1 = match.group(1).strip()
                        req1 = match.group(2).strip() if match.group(2) else ''
                        type2 = match.group(3).strip()
                        req2 = match.group(4).strip() if match.group(4) else ''
                        result = match.group(5).strip()
                        atk = match.group(6) if match.group(6) else '?'
                        defense = match.group(7) if match.group(7) else '?'
                        
                        # Normalizar nomes de tipos
                        type1_normalized = self.normalize_type(type1)
                        type2_normalized = self.normalize_type(type2)
                        
                        if type1_normalized and type2_normalized:
                            self.general_fusions.append({
                                'type1': type1_normalized,
                                'type2': type2_normalized,
                                'result': result,
                                'atk': atk,
                                'def': defense,
                                'req1': req1,
                                'req2': req2
                            })
    
    def normalize_type(self, type_name):
        """Normaliza nomes de tipos para corresponder aos tipos válidos"""
        type_map = {
            'Beast': 'Beast',
            'Warrior': 'Warrior',
            'Dragon': 'Dragon',
            'Dino': 'Dinosaur',
            'Metal': 'Machine',
            'Machine': 'Machine',
            'Plant': 'Plant',
            'Pyro': 'Pyro',
            'Rock': 'Rock',
            'Spellcaster': 'Spellcaster',
            'Thunder': 'Thunder',
            'Water': 'Aqua',
            'Zombie': 'Zombie',
            'Fairy': 'Fairy',
            'Fiend': 'Fiend',
            'Fish': 'Fish',
            'Insect': 'Insect',
            'Reptile': 'Reptile',
            'Winged Beast': 'Winged Beast',
            'WingedBeast': 'Winged Beast',
            'Female': 'Fairy',
        }
        return type_map.get(type_name, type_name if type_name in self.valid_monster_types else None)
    
    def build_fusion_results_map(self):
        """Constrói um mapa reverso: resultado -> combinações que o geram"""
        # Adicionar fusões específicas de cartas
        for card1, fusions in self.card_fusions.items():
            for fusion in fusions:
                result = fusion['result']
                if result not in self.fusion_results:
                    self.fusion_results[result] = []
                
                # Obter stats da carta1
                stats1 = self.card_stats.get(card1, ('?', '?'))
                
                self.fusion_results[result].append({
                    'type': 'specific',
                    'card1': card1,
                    'card1_atk': stats1[0],
                    'card1_def': stats1[1],
                    'card2': fusion['card2'],
                    'card2_atk': fusion['card2_atk'],
                    'card2_def': fusion['card2_def'],
                    'result_atk': fusion['result_atk'],
                    'result_def': fusion['result_def']
                })
        
        # Adicionar fusões gerais
        for fusion in self.general_fusions:
            result = fusion['result']
            if result not in self.fusion_results:
                self.fusion_results[result] = []
            
            self.fusion_results[result].append({
                'type': 'general',
                'type1': fusion['type1'],
                'type2': fusion['type2'],
                'req1': fusion.get('req1', ''),
                'req2': fusion.get('req2', ''),
                'result_atk': fusion['atk'],
                'result_def': fusion['def']
            })
    
    def extract_card_fusions(self, content):
        """Extrai fusões específicas de cartas individuais"""
        # Dividir por seções de cartas
        # Padrão: Nome da Carta (ATK/DEF) Número\n------------------------------------------
        card_sections = re.split(r'\n([^\n]+)\s+\((\d+)/(\d+)\)\s+(\d+)\s*\n-{40,}', content)
        
        current_card = None
        for i in range(1, len(card_sections), 5):
            if i + 3 < len(card_sections):
                card_name = card_sections[i].strip()
                atk = card_sections[i + 1]
                defense = card_sections[i + 2]
                card_number = card_sections[i + 3]
                fusion_text = card_sections[i + 4] if i + 4 < len(card_sections) else ""
                
                # Armazenar stats da carta
                self.card_stats[card_name] = (atk, defense)
                
                # Extrair fusões desta carta
                fusions = []
                lines = fusion_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if '=' in line and line and not line.startswith('Note:'):
                        # Padrão: Card2 (ATK/DEF) = Result (ATK/DEF)
                        match = re.match(r'([^\(]+)\s*\((\d+)/(\d+)\)\s*=\s*([^\(]+)\s*\((\d+)/(\d+)\)', line)
                        if match:
                            card2, c2_atk, c2_def, result, r_atk, r_def = match.groups()
                            fusions.append({
                                'card2': card2.strip(),
                                'card2_atk': c2_atk,
                                'card2_def': c2_def,
                                'result': result.strip(),
                                'result_atk': r_atk,
                                'result_def': r_def
                            })
                        else:
                            # Padrão alternativo sem stats: Card2 = Result (ATK/DEF)
                            match2 = re.match(r'([^=]+)=\s*([^\(]+)\s*\((\d+)/(\d+)\)', line)
                            if match2:
                                card2, result, r_atk, r_def = match2.groups()
                                fusions.append({
                                    'card2': card2.strip(),
                                    'card2_atk': '?',
                                    'card2_def': '?',
                                    'result': result.strip(),
                                    'result_atk': r_atk,
                                    'result_def': r_def
                                })
                
                if fusions:
                    self.card_fusions[card_name] = fusions
    
    def create_widgets(self):
        """Cria a interface gráfica"""
        # Frame superior para busca
        search_frame = ttk.LabelFrame(self.root, text="Buscar Fusões", padding=10)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        # Campo de busca por nome
        ttk.Label(search_frame, text="Nome da Carta:").grid(row=0, column=0, sticky="w", pady=5)
        self.card_name_entry = ttk.Entry(search_frame, width=40)
        self.card_name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Dropdown de tipos
        ttk.Label(search_frame, text="Ou Tipo:").grid(row=1, column=0, sticky="w", pady=5)
        
        # Extrair tipos únicos das fusões gerais e filtrar apenas tipos válidos
        types = set()
        for fusion in self.general_fusions:
            # Adicionar ambos os tipos da fusão
            types.add(fusion['type1'])
            types.add(fusion['type2'])
        
        # Filtrar apenas tipos válidos de monstros
        valid_types = [t for t in types if t in self.valid_monster_types]
        
        self.card_types = sorted(valid_types)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(search_frame, textvariable=self.type_var, 
                                       values=self.card_types, width=37, state="readonly")
        self.type_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Botões
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=0, column=2, rowspan=2, padx=5, pady=5)
        
        search_btn = ttk.Button(button_frame, text="Buscar Fusões", command=self.search_fusions)
        search_btn.pack(pady=2)
        
        clear_btn = ttk.Button(button_frame, text="Limpar Busca", command=self.clear_search)
        clear_btn.pack(pady=2)
        
        # Frame de resultados
        results_frame = ttk.LabelFrame(self.root, text="Resultados", padding=10)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Área de texto para resultados
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, 
                                                       font=("Consolas", 10))
        self.results_text.pack(fill="both", expand=True)
        
        # Configurar tags para formatação
        self.results_text.tag_configure("title", font=("Consolas", 12, "bold"), foreground="blue")
        self.results_text.tag_configure("subtitle", font=("Consolas", 11, "bold"), foreground="green")
        self.results_text.tag_configure("header", font=("Consolas", 10, "bold"))
        self.results_text.tag_configure("result", foreground="darkgreen")
    
    def clear_search(self):
        """Limpa os campos de busca e os resultados"""
        self.card_name_entry.delete(0, tk.END)
        self.type_var.set('')
        self.type_combo.set('')
        self.results_text.delete(1.0, tk.END)
    
    def search_fusions(self):
        """Realiza a busca de fusões"""
        self.results_text.delete(1.0, tk.END)
        
        card_name = self.card_name_entry.get().strip()
        card_type = self.type_var.get().strip()
        
        if not card_name and not card_type:
            messagebox.showwarning("Atenção", "Digite o nome de uma carta ou selecione um tipo!")
            return
        
        found = False
        
        # Buscar por nome de carta
        if card_name:
            found = self.search_by_card_name(card_name)
        
        # Buscar por tipo
        if card_type:
            if found:
                self.results_text.insert(tk.END, "\n" + "="*80 + "\n\n")
            found = self.search_by_type(card_type) or found
        
        if not found:
            self.results_text.insert(tk.END, "Nenhuma fusão encontrada.\n")
    
    def search_by_card_name(self, card_name):
        """Busca fusões de uma carta específica"""
        found = False
        
        # Buscar correspondências exatas ou parciais nas cartas que podem fusionar
        matches = []
        for card in self.card_fusions.keys():
            if card_name.lower() in card.lower():
                matches.append(card)
        
        # Exibir fusões que a carta pode fazer
        for card in matches:
            found = True
            stats = self.card_stats.get(card, ("?", "?"))
            
            self.results_text.insert(tk.END, f"═══════════════════════════════════════════\n", "title")
            self.results_text.insert(tk.END, f"{card} ({stats[0]}/{stats[1]})\n", "title")
            self.results_text.insert(tk.END, f"═══════════════════════════════════════════\n\n", "title")
            
            fusions = self.card_fusions[card]
            self.results_text.insert(tk.END, f"Fusões que {card} pode fazer: {len(fusions)}\n\n", "subtitle")
            
            for i, fusion in enumerate(fusions, 1):
                self.results_text.insert(tk.END, f"{i}. ", "header")
                self.results_text.insert(tk.END, f"{card} ({stats[0]}/{stats[1]})")
                self.results_text.insert(tk.END, " + ")
                
                if fusion['card2_atk'] != '?':
                    self.results_text.insert(tk.END, 
                        f"{fusion['card2']} ({fusion['card2_atk']}/{fusion['card2_def']})")
                else:
                    self.results_text.insert(tk.END, f"{fusion['card2']}")
                
                self.results_text.insert(tk.END, " = ")
                self.results_text.insert(tk.END, 
                    f"{fusion['result']} ({fusion['result_atk']}/{fusion['result_def']})\n", 
                    "result")
            
            self.results_text.insert(tk.END, "\n")
        
        # Buscar se a carta é um resultado de fusão
        result_matches = []
        for result_name in self.fusion_results.keys():
            if card_name.lower() in result_name.lower():
                result_matches.append(result_name)
        
        # Exibir combinações que geram esta carta como resultado
        for result in result_matches:
            if found:
                self.results_text.insert(tk.END, "\n")
            
            found = True
            combinations = self.fusion_results[result]
            
            self.results_text.insert(tk.END, f"═══════════════════════════════════════════\n", "title")
            self.results_text.insert(tk.END, f"Combinações que geram: {result}\n", "title")
            self.results_text.insert(tk.END, f"═══════════════════════════════════════════\n\n", "title")
            
            self.results_text.insert(tk.END, f"Total: {len(combinations)} combinações\n\n", "subtitle")
            
            for i, combo in enumerate(combinations, 1):
                self.results_text.insert(tk.END, f"{i}. ", "header")
                
                if combo['type'] == 'specific':
                    # Fusão específica
                    self.results_text.insert(tk.END, 
                        f"{combo['card1']} ({combo['card1_atk']}/{combo['card1_def']})")
                    self.results_text.insert(tk.END, " + ")
                    
                    if combo['card2_atk'] != '?':
                        self.results_text.insert(tk.END, 
                            f"{combo['card2']} ({combo['card2_atk']}/{combo['card2_def']})")
                    else:
                        self.results_text.insert(tk.END, f"{combo['card2']}")
                else:
                    # Fusão geral
                    self.results_text.insert(tk.END, f"[{combo['type1']}]")
                    if combo.get('req1'):
                        self.results_text.insert(tk.END, f" {combo['req1']}", "header")
                    
                    self.results_text.insert(tk.END, " + ")
                    
                    self.results_text.insert(tk.END, f"[{combo['type2']}]")
                    if combo.get('req2'):
                        self.results_text.insert(tk.END, f" {combo['req2']}", "header")
                
                self.results_text.insert(tk.END, " = ")
                self.results_text.insert(tk.END, 
                    f"{result} ({combo['result_atk']}/{combo['result_def']})\n", 
                    "result")
            
            self.results_text.insert(tk.END, "\n")
        
        if not found:
            self.results_text.insert(tk.END, f"Carta '{card_name}' não encontrada.\n")
        
        return found
    
    def search_by_type(self, card_type):
        """Busca fusões gerais de um tipo"""
        found = False
        
        self.results_text.insert(tk.END, f"═══════════════════════════════════════════\n", "title")
        self.results_text.insert(tk.END, f"Fusões Gerais com [{card_type}]\n", "title")
        self.results_text.insert(tk.END, f"═══════════════════════════════════════════\n\n", "title")
        
        # Buscar fusões onde o tipo aparece
        matching_fusions = []
        for fusion in self.general_fusions:
            if fusion['type1'] == card_type or fusion['type2'] == card_type:
                matching_fusions.append(fusion)
        
        if matching_fusions:
            found = True
            self.results_text.insert(tk.END, f"Total: {len(matching_fusions)} fusões\n\n", "subtitle")
            
            for i, fusion in enumerate(matching_fusions, 1):
                self.results_text.insert(tk.END, f"{i}. ", "header")
                
                # Tipo 1 com requisito
                self.results_text.insert(tk.END, f"[{fusion['type1']}]")
                if fusion.get('req1'):
                    self.results_text.insert(tk.END, f" {fusion['req1']}", "header")
                
                self.results_text.insert(tk.END, " + ")
                
                # Tipo 2 com requisito
                if fusion['type2'].startswith('[') or fusion['type2'] in self.valid_monster_types:
                    self.results_text.insert(tk.END, f"[{fusion['type2']}]")
                else:
                    self.results_text.insert(tk.END, fusion['type2'])
                if fusion.get('req2'):
                    self.results_text.insert(tk.END, f" {fusion['req2']}", "header")
                
                self.results_text.insert(tk.END, " = ")
                
                # Resultado
                if fusion['atk'] != '?':
                    self.results_text.insert(tk.END, 
                        f"{fusion['result']} ({fusion['atk']}/{fusion['def']})\n", 
                        "result")
                else:
                    self.results_text.insert(tk.END, 
                        f"{fusion['result']}\n", 
                        "result")
        else:
            self.results_text.insert(tk.END, f"Nenhuma fusão geral encontrada para [{card_type}].\n")
        
        return found


def main():
    root = tk.Tk()
    app = YugiohFusionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
