# Baku Agentic Football — 5v5

Bir qapıçı və dörd meydan oyunçusundan ibarət AWS futbol komandası. Tövsiyə edilən versiya V4 paketində saxlanılmış əvvəlki V3 davranışıdır: `formation: original`, 1–1–2-yə yaxın mobil quruluş. Səkkiz yeni düzülüşün sınağı ayrıca sənədləşdirilib.

Bu sistem mövqe, topa sahiblik, ötürmə, zərbə və müdafiə qaydalarını istəyə bağlı LLM seçimləri ilə birləşdirir. Kaggle çempionunun çəkiləri bu sistemə köçürülməyib.

## Ölçülmüş nəticə

276 tam yerli AgentPitch matçı keçirilib: 4 nəzarət yoxlaması, 144 ilkin seçim, 48 doğrulama və 80 yekun matç. Hər komandada cəmi **5 oyunçu** var.

Eyni native rəqibə qarşı ayrıca yekun sınaq:

| Davranış | Oyun | Qələbə | Heç-heçə | Məğlubiyyət | Qollar |
|---|---:|---:|---:|---:|---:|
| Saxlanılmış əvvəlki versiya | 20 | 4 | 15 | 1 | 5:1 |
| Eksperimental 2–1–1 | 20 | 0 | 20 | 0 | 0:0 |

Yeni variantın qələbə faizini artırdığı təsdiqlənmədiyi üçün əsas seçim dəyişdirilmədi. Bu 20%-lik nəticə yalnız həmin yerli oyun dəstinə aiddir; AWS yarışında qələbə ehtimalı deyil. Əvvəlki 5%-lik nəticə ilə fərqli toxumlarda alınmış eyni davranış müqayisə olunur, model yaxşılaşması kimi təqdim edilmir.

- [Tam nəticələr və səhvlərin təhlili](reports/NETICELER_AZ.md)
- [YouTube, Kaggle, Reddit, X və futzal mənbələrinin araşdırması](reports/ARASDIRMA_AZ.md)
- [276 matçın nəticəsi](reports/ALL_MATCHES.csv)
- [Saxlanılan versiyanın ilk yekun matçı: 1:0](reports/replay-recommended-first.html)
- [Yekun doğrulama qeydi](reports/FINAL_VERIFICATION.json)

Təkrarları endirib brauzerdə açmaq olar. Qələbə ilə yanaşı ilk eksperimental heç-heçə və məğlubiyyət də `reports/` daxilində saxlanıb. 94 MB-lıq xam matç arxivi repozitoriyaya daxil edilməyib. Tarixi hesabatlardakı workspace runner yolları yerli təcrübə mühitinə aiddir; bu repo tam matç laboratoriyasını deyil, tövsiyə edilən agentləri, testləri və nəticə sübutlarını saxlayır. `reports/original-package-snapshot.json` orijinal tam yerli paketin inventarıdır; Git checkout inventarı deyil.

## Başlamaq

Python 3.12 və ya yenisi:

```sh
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-runtime.txt
python -m pip install httpx
python -m unittest discover -s tests
```

Yüklənən mənbədə 57 test keçib. SDK asılılıqları yoxdursa, SDK testləri ötürülür. Testlər real AWS/Bedrock sorğusu göndərmir.

Beş oyunçu üçün offline nümunə qərar:

```sh
python -m baku_fc.cli fixtures/new-home.json --all
```

Bu əmr offline qərar yoxlamasıdır, futbol matçı deyil.

## Profillər və beş runtime

- `profiles/agentpitch-validated.json`: yerli 100×60 meydan üçün ölçülmüş, LLM-siz profil. Kod+konfiqurasiya izi: `20fb44b0a4e059c3`.
- `profiles/aws-candidate.json`: AWS üçün 110×70 meydan fərziyyəsi ilə hazırlanmış, LLM aktiv namizəd. **Canlı AWS matçında yoxlanmayıb.** Əsas `baku_fc/settings.json` bu profilə uyğundur.
- `profiles/agentpitch-experimental-2-1-1.json`: tövsiyə edilməyən müqayisə profili.

Beş runtime mənbəyini yerli qurmaq:

```sh
python tools/build_agents.py
```

Bu əmr AWS-ə deploy etmir. Nəticə `deployment/build/` daxilində yaranır və Git-ə daxil edilmir. Quraşdırmadan sonra `deployment/build/DEPLOY.txt` və [AWS şablonunun mənşə qeydi](deployment/template/PROVENANCE.md) ilə işləyin. Rəsmi yarışın payload-u, əmr formatı, meydan ölçüləri və gecikmə həddi canlı mühitdə ayrıca təsdiqlənməlidir.

## Mənbə və lisenziya

Öz kodumuz və saxlanılan AWS şablonu üçün MIT-0 bildirişləri qorunub. Təkrarların AgentPitch görüntüləyicisi Apache-2.0 lisenziyalıdır; [üçüncü tərəf bildirişləri](third_party/README.md) saxlanıb. [Mənbə siyahısı](SOURCES.json), [lisenziya](LICENSE.txt) və [araşdırma qeydləri](STRATEGIYA_REFERANSLARI_AZ.md) repozitoriyadadır. Raw Beast-in lisenziyası qeyri-müəyyən faylları və üçüncü tərəf model çəkiləri daxil edilməyib.
