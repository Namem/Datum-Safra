from django.db import models

class SafraAnual(models.Model):
    ano = models.IntegerField(
        verbose_name="Ano da Safra",
        help_text="Ano de início da safra agrícola."
    )
    uf=models.CharField(
        max_length=2,
        verbose_name="Estado (UF)",
        help_text="Sigla da Unidade Federativa (UF)."
    )
    produto = models.CharField(
        max_length=255,
        verbose_name="Produto Agricola",
        help_text="Nome da cultura (ex: Soja, Milho)."

    )
    area_plantada_ha = models.FloatField(
        verbose_name="Área Plantada (ha)",
        help_text="Área plantada em hectares."
        ,null=True, blank=True
    )
    producao_toneladas = models.FloatField(
        verbose_name="Produção (t)",
        help_text="Produção em toneladas."
        ,null=True, blank=True
    )
    produtividade_kg_ha = models.FloatField(
        verbose_name="Produtividade (kg/ha)",
        help_text="Produtividade em quilogramas por hectare."
        ,null=True, blank=True
    )
    class Meta:
        verbose_name = "Safra Anual"
        verbose_name_plural = "Safras Anuais"
        unique_together = ('ano', 'uf', 'produto')
    
    def __str__(self):
        return f"{self.produto} em {self.uf} - Safra {self.ano}"
    


class EstacaoMeteorologica(models.Model):
    """
    Representa uma estação meteorológica do INMET.
    """

    codigo = models.CharField(
        max_length=10,
        primary_key=True,
        verbose_name="Código da Estação",
        help_text="Código único da estação meteorológica."
    )

    nome=models.CharField(
        max_length=255,
        verbose_name="Nome da Estação",        
    )

    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    data_inicio_operacao = models.DateField(
        verbose_name="Início da Operação",
        help_text="Data de início da operação da estação meteorológica."
    )

    uf = models.CharField(
        max_length=2,
        verbose_name="Estado (UF)",
        help_text="Sigla da Unidade Federativa (UF)."

    )

    class Meta:
        verbose_name = "Estação Meteorológica"
        verbose_name_plural = "Estações Meteorológicas"

    def __str__(self):
        return f"{self.nome} ({self.codigo})"
    
class DadoMeteorologicoDiario(models.Model):
    """
    Armazena os dados meteorológicos consolidados para um dia
    em uma determinada estação.
    """

    estacao = models.ForeignKey(
        EstacaoMeteorologica ,
        on_delete=models.CASCADE,
        verbose_name="Estação Meteorológica",
        help_text="A estação à qual este dado pertence."
    )

    data = models.DateField(
        verbose_name="Data da Medição"
    )

    precipitacao_mm = models.FloatField(
        verbose_name="Precipitação (mm)",
        null=True, blank=True
    )

    temp_maxima_c = models.FloatField(
        verbose_name="Temperatura Máxima (°C)",
        null=True, blank=True
    )

    emp_minima_c = models.FloatField(
        verbose_name="Temperatura Mínima (°C)",
        null=True, blank=True
    )

    umidade_media_porc = models.FloatField(
        verbose_name="Umidade Média (%)",
        null=True, blank=True
    )

    class Meta:
        verbose_name = "Dado Meteorológico Diário"
        verbose_name_plural = "Dados Meteorológicos Diários"
        # Garante que só teremos um registro por dia por estação.
        unique_together = ('estacao', 'data')
    def __str__(self):
        return f"Dados de {self.estacao.codigo} para {self.data.strftime('%Y-%m-%d')}"



                        


