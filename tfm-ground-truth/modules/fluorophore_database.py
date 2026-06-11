"""常用荧光基团光谱参数数据库（激发/发射波长、量子产率、消光系数）。"""

# 荧光基团数据库
FLUOROPHORE_DATABASE = {
    "FITC": {
        "name": "Fluorescein isothiocyanate",
        "excitation": 495,  # nm
        "emission": 519,    # nm
        "quantum_yield": 0.93,
        "extinction_coefficient": 73000,  # M^-1 cm^-1
        "application": "绿色荧光，常用于标记蛋白质"
    },
    "GFP": {
        "name": "Green Fluorescent Protein",
        "excitation": 488,
        "emission": 507,
        "quantum_yield": 0.79,
        "extinction_coefficient": 55000,
        "application": "生物发光蛋白，广泛用于活细胞成像"
    },
    "Texas Red": {
        "name": "Texas Red",
        "excitation": 595,
        "emission": 615,
        "quantum_yield": 0.51,
        "extinction_coefficient": 85000,
        "application": "红色荧光，用于多色标记"
    },
    "Cy3": {
        "name": "Cyanine 3",
        "excitation": 550,
        "emission": 570,
        "quantum_yield": 0.15,
        "extinction_coefficient": 150000,
        "application": "橙色荧光，光稳定性好"
    },
    "Cy5": {
        "name": "Cyanine 5",
        "excitation": 650,
        "emission": 670,
        "quantum_yield": 0.28,
        "extinction_coefficient": 250000,
        "application": "远红荧光，背景低"
    },
    "mCherry": {
        "name": "mCherry",
        "excitation": 587,
        "emission": 610,
        "quantum_yield": 0.22,
        "extinction_coefficient": 72000,
        "application": "红色荧光蛋白，pH稳定"
    },
    "DAPI": {
        "name": "4',6-diamidino-2-phenylindole",
        "excitation": 358,
        "emission": 461,
        "quantum_yield": 0.6,
        "extinction_coefficient": 27000,
        "application": "蓝色荧光，DNA染色"
    },
    "mNeonGreen": {
        "name": "mNeonGreen",
        "excitation": 506,
        "emission": 517,
        "quantum_yield": 0.80,
        "extinction_coefficient": 116000,
        "application": "亮绿色荧光蛋白，高亮度"
    },
    "Alexa Fluor 488": {
        "name": "Alexa Fluor 488",
        "excitation": 495,
        "emission": 519,
        "quantum_yield": 0.92,
        "extinction_coefficient": 71000,
        "application": "绿色荧光，光稳定性极佳"
    },
    "Alexa Fluor 594": {
        "name": "Alexa Fluor 594",
        "excitation": 590,
        "emission": 617,
        "quantum_yield": 0.66,
        "extinction_coefficient": 92000,
        "application": "红色荧光，光稳定性极佳"
    },
    "Custom": {
        "name": "Custom Fluorophore",
        "excitation": 530,
        "emission": 560,
        "quantum_yield": 0.5,
        "extinction_coefficient": 50000,
        "application": "自定义参数"
    }
}


def get_fluorophore_info(fluorophore_name):
    """
    获取荧光基团信息
    
    参数:
        fluorophore_name (str): 荧光基团名称
    
    返回:
        dict: 荧光基团参数
    """
    return FLUOROPHORE_DATABASE.get(fluorophore_name, FLUOROPHORE_DATABASE["Custom"])


def list_all_fluorophores():
    """
    列出所有可用的荧光基团
    
    返回:
        list: 荧光基团名称列表
    """
    return list(FLUOROPHORE_DATABASE.keys())


def get_excitation_emission(fluorophore_name):
    """
    获取激发和发射波长
    
    参数:
        fluorophore_name (str): 荧光基团名称
    
    返回:
        tuple: (excitation_wavelength, emission_wavelength) in nm
    """
    info = get_fluorophore_info(fluorophore_name)
    return info['excitation'], info['emission']

