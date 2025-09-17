from django.shortcuts import render
from django.http import JsonResponse
from .models import SafraAnual, DadoMeteorologicoDiario
from django.db.models import Sum, Avg

def dashboard_view(request):
    """
    Renderiza a página principal do dashboard.
    """
    # Por enquanto, apenas renderizamos o template.
    
    return render(request, 'core/dashboard.html')


def get_chart_data(request):
    """
    Fornece os dados agregados para o gráfico, agora aceitando filtros.
    """
    # Pega os parâmetros da URL, com um valor padrão 'soja'
    produto_filtrado = request.GET.get('produto', 'soja')

    # Constrói a query base
    query_producao = SafraAnual.objects.all()

    # Aplica o filtro de produto se ele foi especificado
    if produto_filtrado:
        query_producao = query_producao.filter(produto__icontains=produto_filtrado)

    # Agrega os dados
    producao_anual = query_producao.values('ano').annotate(
        total_producao=Sum('producao_toneladas')
    ).order_by('ano')

    precipitacao_anual = DadoMeteorologicoDiario.objects.values('data__year').annotate(
        total_precipitacao=Sum('precipitacao_mm')
    ).order_by('data__year')

    producao_dict = {item['ano']: item['total_producao'] for item in producao_anual}
    precipitacao_dict = {item['data__year']: item['total_precipitacao'] for item in precipitacao_anual}

    labels = sorted(list(set(producao_dict.keys()) & set(precipitacao_dict.keys())))

    # Define um nome dinâmico para o gráfico baseado no filtro
    label_producao = f'Produção de {produto_filtrado.capitalize()} (Toneladas)'

    data = {
        'labels': labels,
        'datasets': [
            {
                'label': label_producao,
                'data': [producao_dict.get(ano) for ano in labels],
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1,
                'yAxisID': 'y-producao',
            },
            {
                'label': 'Precipitação Total (mm)',
                'data': [precipitacao_dict.get(ano) for ano in labels],
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1,
                'yAxisID': 'y-precipitacao',
            }
        ]
    }
    return JsonResponse(data)