"""
Script para popular casos de treino no banco de dados
Execute: python seed_training_cases.py
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models import TrainingCase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://golpe_user:golpe_pass@localhost:5432/golpe_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

training_cases = [
    {
        "title": "Phishing de Banco Falso",
        "description": "Site que imita página de login de banco solicitando credenciais",
        "payload_url": "https://exemplo-golpe.com/login-banco",
        "lesson": {
            "tips": [
                "Sempre verifique o domínio completo antes de inserir dados",
                "Bancos legítimos nunca pedem senha completa por email/SMS",
                "Procure pelo cadeado verde e certificado SSL válido"
            ],
            "signals": [
                "Domínio similar mas diferente do oficial",
                "Formulário pedindo senha completa",
                "Certificado SSL inválido"
            ]
        }
    },
    {
        "title": "Golpe de Loteria",
        "description": "Site falso anunciando prêmio de loteria",
        "payload_url": "https://exemplo-golpe.com/loteria-premio",
        "lesson": {
            "tips": [
                "Nunca acredite em prêmios que você não participou",
                "Desconfie de sites que pedem dados pessoais para 'liberar prêmio'",
                "Verifique sempre a autenticidade do site oficial"
            ],
            "signals": [
                "Promessa de prêmio sem participação",
                "Solicitação de dados bancários",
                "Urgência para 'resgatar prêmio'"
            ]
        }
    },
    {
        "title": "Phishing de E-commerce",
        "description": "Site falso imitando loja online conhecida",
        "payload_url": "https://exemplo-golpe.com/loja-falsa",
        "lesson": {
            "tips": [
                "Verifique sempre a URL completa da loja",
                "Desconfie de preços muito abaixo do mercado",
                "Procure por avaliações e certificações de segurança"
            ],
            "signals": [
                "Preços suspeitamente baixos",
                "Forma de pagamento apenas por transferência",
                "Ausência de informações de contato"
            ]
        }
    }
]

def seed_training_cases():
    db = SessionLocal()
    try:
        # Limpar casos existentes (opcional)
        # db.query(TrainingCase).delete()
        
        for case_data in training_cases:
            # Verificar se já existe
            existing = db.query(TrainingCase).filter(
                TrainingCase.title == case_data["title"]
            ).first()
            
            if not existing:
                case = TrainingCase(**case_data)
                db.add(case)
                print(f"✅ Adicionado: {case_data['title']}")
            else:
                print(f"⏭️  Já existe: {case_data['title']}")
        
        db.commit()
        print("\n✅ Casos de treino populados com sucesso!")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao popular casos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_training_cases()

