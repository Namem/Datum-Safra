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


