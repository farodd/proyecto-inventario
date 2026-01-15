import json

def estandarizar_datos(df, metadata_path='../metadata/metadata_insumos.json'):
    """Estandariza clasificación y unidades usando metadata"""
    with open(metadata_path, 'r', encoding='utf-8') as file:
        metadata = json.load(file)
    
    df_result = df.copy()
    categoria_map = {}
    unidad_map = {}
    
    # Crear mapeos
    for categoria_std, info in metadata.get('categorias', {}).items():
        categoria_map[categoria_std] = categoria_std
        for variacion in info.get('variaciones', []):
            categoria_map[variacion] = categoria_std
    
    for unidad_std, info in metadata.get('unidades_medida', {}).items():
        unidad_map[unidad_std] = unidad_std
        for variacion in info.get('variaciones', []):
            unidad_map[variacion] = unidad_std


    if 'UM' in df_result.columns:
        df_result['UM'] = df_result['UM'].str.strip()
        df_result['UM'] = df_result['UM'].map(unidad_map)
        print("✅ Unidades estandarizadas")

    if 'CLASIFICACION' in df_result.columns:
        df_result['CLASIFICACION'] = df_result['CLASIFICACION'].str.strip()
        df_result['CLASIFICACION'] = df_result['CLASIFICACION'].map(categoria_map)
        print("✅ Clasificación estandarizada")

    
    return df_result, df_result['CLASIFICACION'].unique(), df_result['UM'].unique()