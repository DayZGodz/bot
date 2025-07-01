import os

def get_env_id(env_var_name: str) -> int:
    """
    Obtém um ID do Discord de uma variável de ambiente.
    
    Args:
        env_var_name (str): Nome da variável de ambiente
        
    Returns:
        int: ID do Discord ou 0 se não encontrado
    """
    try:
        return int(os.getenv(env_var_name, '0'))
    except ValueError:
        print(f"❌ Erro ao converter {env_var_name} para ID")
        return 0 