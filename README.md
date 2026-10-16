# Baku Agentic Football — 5v5 faza taktikaları

Bir qapıçı və dörd meydan oyunçusu. Hücum, müdafiə və topa sahiblik keçidləri üçün ayrı qərar qaydaları. V5 taktika genişləndirməsi və onun ölçülmüş nəticələri bu repozitoriyadadır.

Yekun qəbul şərtini keçən yeni profil əsas seçimdir.

## Yeni davranışlar

- Geridən çıxışda 1–2–1, irəliləyişdə 1–1–2; ayrı kanallar və fərqli dərinlikli qaçışlar.
- Topun arxasını sığortalayan oyunçunun rola görə dəyişməsi.
- Hücumda genişlik variantı, son zonada uzaq cinahın daralması və açıq ötürmə xəttinə dəstək.
- Top rəqibdə olanda yığcam blok, top tərəfə sürüşmə və təhlükəli oyunçunun qapı tərəfdən tutulması.
- Cinah/məsafə/örtük şərtləri ilə press; yaxınlaşma ilə birbaşa topa müdaxilə ayrı əmrlərdir.
- Yerli dəstək varsa qısa əks-press, top qazanıldıqda hücuma sürətli keçid.
- Hesab, məlum qalan vaxt, stamina, aktiv oyunçu sayı və ofsayd həddi ilə riskin idarəsi.

Bunlar qaydalarla qurulmuş taktikalardır. Bütün xüsusiyyətlərin birlikdə faydalı olduğu iddia edilmir; ayrıca variantlar sınaqdan keçirilib. [Qaydalar və FIFA mənbələri](TAKTIKA_AZ.md).

## Nəticələr

216 tam nəzarətli yerli matç: 4 nəzarət yoxlaması, 96 ilkin seçim, 36 doğrulama və 80 yekun oyun. İlkin inteqrasiya pilotu bu saydan ayrıdır.

Yekun dəstdə seçilmiş yeni variant: **t_attack**. Tövsiyə edilən əsas parametr: **`phase_tactics: attack`**.

| Variant / rəqib | Oyun | Q | H | M | Qollar |
|---|---:|---:|---:|---:|---:|
| t_off / baseline | 20 | 2 | 16 | 2 | 3:2 |
| t_attack / baseline | 20 | 4 | 13 | 3 | 4:3 |
| t_off / reference3 | 20 | 4 | 12 | 4 | 5:5 |
| t_attack / reference3 | 20 | 7 | 10 | 3 | 11:3 |

Bu faizlər yerli AgentPitch rəqiblərinə aiddir. Canlı AWS/LLM matçlarında yoxlanmayıb; AWS çempionlarının agentləri rəqib kimi istifadə edilməyib.

İki rəqib üzrə qələbələr 6/40-dan 11/40-a yüksəlib. Cüt toxumlar üzrə fərqin bootstrap 95% intervalı −5 ilə +30 faiz bəndidir: nəticə ümidvericidir, lakin statistik qeyri-müəyyənlik genişdir. Native rəqibin bir snapshot xətası üçün hər iki versiya və tərəf təkrar yoxlanıb; [audit qeydi](reports/phase-v5/BENCHMARK_REPAIR.json) saxlanıb.

- [Tam V5 nəticələri və təhlil](reports/phase-v5/NETICELER_AZ.md)
- [216 matçın cədvəli](reports/phase-v5/ALL_MATCHES.csv)
- [Faktiki mövqelənmə və hücum göstəriciləri](reports/phase-v5/DIAGNOSTICS.json)
- [İlk yekun matçın təkrarı](reports/phase-v5/replay-first.html)
- [Əvvəlki V4 hesabatı](reports/NETICELER_AZ.md)

Təkrarları endirib brauzerdə açın. Xam ZIP matç arxivləri yerli outputs qovluğunda saxlanır.

## Başlamaq

Python 3.12 və ya yenisi:

```sh
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-runtime.txt
python -m pip install httpx
python -m unittest discover -s tests
python -m baku_fc.cli fixtures/new-home.json --all
```

**67 test keçirilib, ötürülmüş test yoxdur.** Testlər real AWS sorğusu göndərmir. Son əmr beş oyunçunun offline qərar yoxlamasıdır, tam futbol matçı deyil.

## Profillər

`profiles/phase-*.json` yerli 100×60 meydan üçün seçimlərdir: `off`, `attack`, `compact`, `trigger`, `high`, `complete`, `wide`, `pivot`. `phase_tactics` parametrini profilə görə dəyişin. Əsas yerli profil `profiles/agentpitch-validated.json`; mənbə+konfiqurasiya izi `f3522a2a0850b428`.

`profiles/aws-candidate.json` və əsas settings 110×70 meydan fərziyyəsi ilə AWS namizədidir. `profiles/aws-experimental-phase.json` seçilmiş yeni taktikanın AWS namizədidir. Canlı yarışın payload-u, ölçüləri, əmrləri və gecikməsi ayrıca uyğunlaşdırılmalıdır.

Beş runtime mənbəyini yerli qurmaq:

```sh
python tools/build_agents.py
```

Bu əmr deploy etmir. `deployment/build/DEPLOY.txt` və [şablonun mənşə qeydi](deployment/template/PROVENANCE.md) sonrakı quraşdırmanı izah edir. Quraşdırılmış fayllar Git-ə daxil edilmir.

## Mənbələr

Öz kodu və AWS şablonu MIT-0; təkrarların AgentPitch görüntüləyicisi Apache-2.0-dır. [Mənbələr](SOURCES.json), [üçüncü tərəf bildirişləri](third_party/README.md), [lisenziya](LICENSE.txt). Üçüncü tərəf Kaggle çəkiləri daxil edilməyib.
