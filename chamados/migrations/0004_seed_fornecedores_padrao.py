from django.db import migrations


FORNECEDORES_PADRAO = [
    "EQS Engenharia",
    "ACT Power",
    "Novo Brasil",
    "Scovan",
    "Top Service",
    "Base",
    "Viva",
    "N/A",
]


def criar_fornecedores_padrao(apps, schema_editor):
    from django.db import transaction
    Fornecedor = apps.get_model("chamados", "Fornecedor")
    with transaction.atomic():
        for nome in FORNECEDORES_PADRAO:
            Fornecedor.objects.get_or_create(nome=nome, defaults={"ativo": True})


def remover_fornecedores_padrao(apps, schema_editor):
    Fornecedor = apps.get_model("chamados", "Fornecedor")
    Fornecedor.objects.filter(nome__in=FORNECEDORES_PADRAO).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("chamados", "0003_obra"),
    ]

    operations = [
        migrations.RunPython(criar_fornecedores_padrao, remover_fornecedores_padrao),
    ]
