import sys
import os

# Garante que a saída do terminal use UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Define as pastas base
core_base_path = os.path.join(os.getcwd(), "Content/_Core")
splash_path = os.path.join(os.getcwd(), "Content/Splash")

# Dicionário com descrições para os arquivos Guide.txt (Inglês / Português)
descriptions = {
    "Art/Materials": ("This folder contains all materials used in the game, including shaders and material instances.",
                      "Esta pasta contém todos os materiais utilizados no jogo, incluindo shaders e instâncias de materiais."),
    "Art/Textures": ("This folder contains all game textures. Organize them by resolution and type for easy access.",
                     "Aqui ficam todas as texturas do jogo. Organize por resolução e tipo para facilitar o acesso."),
    "Art/Meshes": ("This folder contains all 3D models (static and dynamic) used in the game.",
                   "Esta pasta contém todos os modelos 3D (estáticos e dinâmicos) usados no jogo."),
    "Art/Animations": ("Store all character animations, rigs, and montages here.",
                       "Guarde todas as animações de personagens, rigs e montagens nesta pasta."),
    "Art/VFX": ("Visual effects such as sprites, shaders, and particle effects are stored here.",
                "Efeitos visuais, como sprites, shaders e efeitos de partículas, são armazenados aqui."),
    "Audio/Music": ("Background music and soundtracks are stored in this folder.",
                    "Trilhas sonoras e músicas de fundo do jogo são armazenadas nesta pasta."),
    "Audio/SFX": ("This folder contains sound effects like footsteps, gunshots, and ambient sounds.",
                  "Aqui ficam os efeitos sonoros, como passos, tiros e sons ambientes."),
    "Audio/Voice": ("All voiceover and dialogue files should be stored here.",
                    "Todos os arquivos de dublagem e diálogos devem ser mantidos aqui."),
    "Blueprints/Core": ("Contains essential Blueprints for the game's core functionality.",
                        "Contém os Blueprints essenciais para a base do jogo."),
    "Blueprints/Gameplay": ("Store Blueprints related to game mechanics here.",
                            "Guarde aqui os Blueprints específicos para mecânicas de jogo."),
    "Blueprints/UI": ("Blueprints responsible for the user interface.",
                      "Blueprints responsáveis pela interface do usuário."),
    "Config": ("Stores game configuration files, such as DefaultGame.ini and Engine.ini.",
               "Armazena arquivos de configuração do jogo, como DefaultGame.ini e Engine.ini."),
    "Maps/Main": ("This is the game's main map.",
                  "Este é o mapa principal do jogo."),
    "Maps/Levels": ("This folder contains secondary maps and additional game levels.",
                    "Mapas secundários e fases adicionais do jogo são armazenados aqui."),
    "Maps/Test": ("Maps used for testing and debugging.",
                  "Mapas usados para testes e depuração do jogo."),
    "UI/Widgets": ("All UMG Widgets used for menus and HUD are stored here.",
                   "Todos os Widgets UMG usados para menus e HUD ficam aqui."),
    "UI/Icons": ("Icons used in the game interface should be organized here.",
                 "Ícones usados na interface do jogo devem ser organizados aqui."),
    "Data/DataTables": ("This folder contains Data Tables used to store structured game data.",
                        "Esta pasta contém Data Tables usadas para armazenar dados estruturados do jogo."),
    "Data/Enums": ("This folder contains all Enums used in the game.",
                   "Aqui ficam os arquivos Enum utilizados no jogo."),
    "Data/Structures": ("UE Structs used to store complex data are kept here.",
                        "Structs do Unreal usadas para armazenar dados complexos são mantidas aqui."),
    "Code/Core": ("Core C++ files essential to the game engine.",
                  "Arquivos C++ essenciais para o núcleo do jogo."),
    "Code/Gameplay": ("C++ scripts related to gameplay mechanics.",
                      "Scripts de C++ relacionados à jogabilidade do jogo."),
    "Code/AI": ("AI logic written in C++.",
                "Lógica de Inteligência Artificial escrita em C++."),
    "Code/UI": ("C++ code responsible for UI interactions.",
                "Código C++ responsável pela interface gráfica."),
    "Cinematics": ("Stores all cutscenes and cinematics sequences.",
                   "Armazena todas as sequências cinematográficas e cutscenes."),
    "FX/Niagara": ("Particle effects created with the Niagara system.",
                   "Efeitos de partículas criados com o sistema Niagara."),
    "FX/Particles": ("Standard Unreal Engine particles.",
                     "Partículas convencionais do Unreal Engine."),
    "Shaders": ("All custom shaders for the game are stored here.",
                "Todos os shaders personalizados para o jogo são mantidos aqui."),
    "ThirdParty": ("Plugins and third-party libraries should be stored here.",
                   "Plugins e bibliotecas de terceiros devem ser armazenados aqui."),
    "Inputs/InputActions": ("This folder contains Input Action assets used to define player input mappings in Unreal Engine. It is essential for handling keybindings, gamepad controls, and other input interactions.",
                   "Esta pasta contém os ativos de Input Action usados para definir os mapeamentos de entrada do jogador no Unreal Engine. É essencial para gerenciar teclas de atalho, controles de gamepad e outras interações de entrada."),
    "Documents": ("Project documentation, diagrams, and important notes.",
                  "Documentação do projeto, diagramas e anotações importantes.")
}

# Criando as pastas dentro de "Content/_Core" e adicionando os arquivos Guide.txt
for folder, description in descriptions.items():
    full_path = os.path.join(core_base_path, folder)
    guide_path = os.path.join(full_path, "Guide.txt")
    
    # Criando a pasta se não existir
    if not os.path.exists(full_path):
        os.makedirs(full_path)
        print(f"📁 Criado: {full_path}")
    else:
        print(f"✅ Já existe: {full_path}")

    # Criando ou sobrescrevendo Guide.txt com descrições em inglês e português
    with open(guide_path, "w", encoding="utf-8") as guide_file:
        guide_file.write(f"{description[0]}\n{description[1]}")
        print(f"📄 Guide.txt criado em: {guide_path}")

# Criando a pasta "Content/Splash" separadamente
if not os.path.exists(splash_path):
    os.makedirs(splash_path)
    print(f"📁 Criado: {splash_path}")
else:
    print(f"✅ Já existe: {splash_path}")

# Criando um Guide.txt dentro de Splash
splash_guide_path = os.path.join(splash_path, "Guide.txt")
with open(splash_guide_path, "w", encoding="utf-8") as splash_guide_file:
    splash_guide_file.write("This folder contains the game's Splash Screen assets.\nEsta pasta contém as telas de Splash Screen do jogo.")
    print(f"📄 Guide.txt criado em: {splash_guide_path}")

print("🎮 Estrutura de pastas criada com sucesso dentro de Content!")
