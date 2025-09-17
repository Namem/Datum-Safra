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
    


class Localidade(models.Model):
    """
    Representa uma localidade (município) com coordenadas geográficas.
    """
    nome = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Nome da Localidade"
    )
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        verbose_name = "Localidade"
        verbose_name_plural = "Localidades"

    def __str__(self):
        return self.nome


class DadoMeteorologicoDiario(models.Model):
    """
    Armazena os dados meteorológicos da NASA para um dia em uma localidade.
    """
    localidade = models.ForeignKey(
        Localidade,
        on_delete=models.CASCADE,
        verbose_name="Localidade",
    )
    data = models.DateField(
        verbose_name="Data da Medição"
    )
    precipitacao_mm = models.FloatField(
        verbose_name="Precipitação Corrigida (mm/dia)",
        null=True, blank=True
    )
    temp_maxima_c = models.FloatField(
        verbose_name="Temperatura Máxima a 2m (°C)",
        null=True, blank=True
    )
    temp_minima_c = models.FloatField(
        verbose_name="Temperatura Mínima a 2m (°C)",
        null=True, blank=True
    )

    class Meta:
        verbose_name = "Dado Meteorológico Diário"
        verbose_name_plural = "Dados Meteorológicos Diários"
        unique_together = ('localidade', 'data')

    def __str__(self):
        return f"Dados de {self.localidade.nome} para {self.data.strftime('%Y-%m-%d')}"