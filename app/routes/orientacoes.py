from fastapi import APIRouter, Depends
from app.security.token import usuario_atual
from app.models.usuario import Usuario

router = APIRouter(prefix='/api/orientacoes', tags=['Orientações gerais'])

@router.get('/rotina')
def rotina(usuario: Usuario = Depends(usuario_atual)):
    return {
      'aviso': 'Orientações educativas, não substituem nutricionista esportivo, médico ou preparador físico. Rotinas e porções devem ser individualizadas.',
      'alimentacao': [
        'Faça refeições regulares com alimentos variados, incluindo fontes de carboidratos, proteínas, frutas e verduras.',
        'Antes do treino, prefira alimentos familiares e de fácil digestão, respeitando o intervalo que funciona para você.',
        'Depois do treino, faça uma refeição ou lanche que contenha carboidratos e proteínas.',
        'Evite dietas restritivas e metas de perda de peso sem acompanhamento profissional.'
      ],
      'hidratacao': [
        'Tenha água disponível ao longo do dia e durante os treinos; as necessidades variam com calor, suor e esforço.',
        'Comunique tontura, fraqueza, dor de cabeça ou mal-estar ao treinador; não force o treino.'
      ],
      'sono': ['Adolescentes geralmente precisam de 8 a 10 horas de sono por noite.', 'Mantenha horários regulares e reduza telas perto da hora de dormir.'],
      'treino': ['Aqueça antes de atividades intensas.', 'A carga deve ser definida pelo treinador conforme maturação, experiência e calendário.', 'Dor, lesão ou cansaço persistente exigem avaliação antes de aumentar a carga.'],
      'futsal': {'goleiro':'técnica de defesa, posicionamento e deslocamentos', 'fixo':'marcação, passe e leitura defensiva', 'ala_direito':'aceleração, mudança de direção e tomada de decisão', 'ala_esquerdo':'aceleração, mudança de direção e tomada de decisão', 'pivo':'proteção da bola, giro e finalização', 'universal':'movimentação, passe e tomada de decisão'}
    }
