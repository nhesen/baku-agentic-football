# Baku FC — sabit V6 (5v5)

Əsas runtime və profillər orijinal V6 kommitindən bərpa edilib. 74 test yenidən keçib; beş runtime qurulub və Python mənbə baytları əvvəlki V6 ilə tutuşdurulub.

[Orijinal V6 ZIP və release](https://github.com/nhesen/baku-agentic-football/releases/tag/v6.0.0). Native fingerprint `72487b5cac201020`, AWS namizədi `c42fb85e84e47400`.

V7 yerli müqayisədə üstünlük göstərmədiyi üçün əsas seçim deyil. V7 kodu `finishing-v7` branch və `v7.0.0` tag-da, [sənədi burada](docs/V7_README.md), nəticələri `reports/finishing-v7` qovluğunda saxlanır. Yeni fərziyyələr ayrıca araşdırılır; sabit V6-ya gizli dəyişiklik edilməyib. Canlı AWS-də yoxlanmayıb.


Bir qapıçı və dörd meydan oyunçusu. İngiliscə real futbol mənbələrindən götürülən prinsiplər native matçlarda ayrıca və birlikdə sınaqdan keçirilib.

Yeni variant əvvəlcədən yazılmış qəbul şərtini keçdiyi üçün əsas profilə seçilib.

## Nə sınanıb

- Ayrı ötürmə bucaqları və açıq xətlər üçün üçbucaq dəstəyi.
- Görünən top sahibliyi ötürüləndən sonra pas verənin diaqonal qaçışı.
- Rəqibi gecikdirən bir müdafiəçi, qapı tərəfi örtüyü və hücuma çıxış.
- Aktiv oyunçu çıxarılanda sığorta rolunun başqa aktiv oyunçuya keçməsi.

[15 ingiliscə mənbə: oxunan hissələr, nəticələr və kod xəritəsi](RESEARCH_AZ.md). Qapıçıdan başqa dörd meydan oyunçusu var; futzalın ayrıca qaydaları mühərrikə əlavə edilməyib.

## Ölçülmüş nəticələr

180 tam yerli matç: 4 nəzarət təkrarı, 60 ilkin seçim, 36 doğrulama və 80 toxunulmamış yekun oyun. Rəqiblər native baseline və dondurulmuş V5 agentimizdir.

| Variant / rəqib | Oyun | Q | H | M | Qollar |
|---|---:|---:|---:|---:|---:|
| c_off / baseline | 20 | 2 | 13 | 5 | 2:5 |
| c_give_go / baseline | 20 | 3 | 14 | 3 | 4:4 |
| c_off / reference5 | 20 | 4 | 12 | 4 | 4:4 |
| c_give_go / reference5 | 20 | 4 | 13 | 3 | 4:3 |

Yekun seçilmiş namizəd `c_give_go`. Qələbə fərqi 2.5 faiz bəndi; toxumları cüt saxlayan bootstrap 95% intervalı [-10.0, 15.0]. Bu nəticə canlı AWS turnirini qazanmaq ehtimalı deyil.

- [Tam nəticələr və dərs](reports/coaching-v6/NETICELER_AZ.md)
- [180 matçın cədvəli](reports/coaching-v6/ALL_MATCHES.csv)
- [Faktiki hücum göstəriciləri](reports/coaching-v6/DIAGNOSTICS.json)
- [Yekun matçın təkrarı](reports/coaching-v6/replay-first.html)
- [Əvvəlki V5 nəticələri](reports/phase-v5/NETICELER_AZ.md)

## İşlətmək

```sh
python -m venv .venv
python -m pip install -r requirements-runtime.txt
python -m pip install httpx
python -m unittest discover -s tests
python tools/build_agents.py
```

74 test keçib, ötürülən yoxdur. Beş runtime yerli qurulub və mənbə baytları yoxlanıb. Build AWS deploy etmir.

Əsas yerli profil: `profiles/agentpitch-validated.json`; parametrlər `phase_tactics=attack`, `combination_tactics=give_go`; fingerprint `72487b5cac201020`. `profiles/coaching-*.json` ayrıca sınaq rejimləridir. AWS namizədi `profiles/aws-candidate.json` və əsas `settings.json` faylıdır: 110×70 meydan fərziyyəsi var, canlı yoxlanmayıb.

Fizika, roster və atributlar dəyişdirilməyib; hər matç 1200 native tick-dir. Mənbə bütün seçim mərhələləri boyunca dondurulub. AWS çempionlarının açıq agentləri, canlı portal və LLM matçları bu müqayisəyə daxil deyil.

## Mənşə və lisenziya

Öz kodu və AWS şablonu MIT-0; təkrarlardakı upstream AgentPitch viewer Apache-2.0-dır. [Mənbələr](SOURCES.json), [bildirişlər](third_party/README.md), [sınaq mənşəyi](reports/coaching-v6/PROVENANCE.json). Xam matç ZIP-i yerli outputs/baku-v6-study qovluğundadır.
