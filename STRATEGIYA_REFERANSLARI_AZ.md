# 5v5 üçün genişləndirilmiş araşdırma — 17 oktyabr 2026

Bu sənəd əvvəlki `baku-v3-study/DERIN_ARASDIRMA_AZ.md` hesabatına əlavədir. Bütün internetin və bütün yarışların tam siyahısını yoxladığımız iddia edilmir. Məqsəd yeni, icra oluna bilən fərziyyələri tapmaq və eyni şərtlərlə matçlarda ölçməkdir. Başqa müəlliflərin faizləri bizim nəticələrimiz deyil.

## Yeni mənbələr və sübutun səviyyəsi

| Mənbə | Faktiki baxılan material | Nəticə və istifadə sərhədi |
|---|---|---|
| [AWS Agentic Football Cup Georgia 2026](https://www.youtube.com/watch?v=fD3HQlH_4E0) | Təsvir, avtomatik transkript, təxminən 1:05 və 2:32 kadrları | Tədbir montajı; transkript əsasən musiqidir. İştirakçı strategiyası və qalib agent kodu çıxarılmadı. |
| [TrickSumo: Virtual League 2026](https://www.youtube.com/watch?v=eEv45nl_jf4) | Tam 1:29 transkript, təsvir, təxminən 0:45 matç kadrı | Beş agentə ayrı təlimat verilməsi və liqa gedişi izah olunur. Konkret qalib promptu və müqayisəli taktika sınağı yoxdur. |
| [Sky High Designs: I coached 5 AI agents…](https://www.youtube.com/watch?v=guspgfDu9n0) | Açılmış tam təsvir, 1:08 matç kadrı və son prompt ekranı | Müəllif ikinci mövsüm üçün 6W–4L, 427 komandadan 30-cu yer bildirir. Bir göstərilən matç Basalt Condors–Tempest Stings 1:0-dır. Tam transkript alınmadı; sondakı prompt mətni oxunaqlı şəkildə çıxarılmadı. |
| [Minds: Beginner’s Guide](https://www.youtube.com/watch?v=zN70Oa-1y8Y) | Açılmış təsvir, təxminən 1:08 komanda yerləşdirmə ekranı | Qeydiyyat/deploy/matç hesabatı dövrünü təsdiqləyir. Taktik üstünlüyə sübut deyil. İlk cəhddə transkript əlçatan olmadı. |
| [DBro: League Match](https://www.youtube.com/watch?v=YmzstuisrTg) | Təsvir, 2:00 və 3:12 matç kadrları | Açıq matç nümunəsidir; agentlərin tam təlimatı yoxdur. Bir neçə kadrdan sabit düzülüş və ümumi qələbə faizi çıxarılmadı. |
| [DBro: AI Football Match](https://www.youtube.com/watch?v=EpsJ2C5hSPw) | Təxminən 2:17 kadrı, səhifə/təsvir | Matç görüntüsündə 1:1 görünür; bu yekun nəticə kimi qeydə alınmadı. Agent faylları təqdim edilmir. |
| [SANGU: Georgia tədbirinin təşkilatçı xəbəri](https://sangu.edu.ge/news/3736/aws-agentic-football-cup-georgia) | Təşkilatçının xəbəri | Tədbir 22 avqust 2026-da keçirilib. Video 23 avqustda yayımlanıb; xəbər 2 sentyabrdadır. Tədbir tarixi ilə paylaşım tarixini qarışdırmırıq. |

Videoların hamısına fasiləsiz, başdan-sona baxıldığı iddia edilmir: yuxarıda hansı transkript, təsvir və seçilmiş kadrın yoxlandığı göstərilib. Kadrlar hərəkətin səbəbini, modelin qərarını və yerinə yetirilmiş əmri təkbaşına izah etmir.

## AWS liqasında 9–1 nəticə göstərən müəllif

[Yinchen Ma / Mayinchen-in orijinal AWS Builder yazısı](https://builder.aws.com/content/3JJgFfqDX0yyBekhcvBdS0Bp39o/how-ai-wins-a-football-match-five-agents-that-never-talk-two-minutes-and-a-failure-report) 14 sentyabrda yayımlanıb, 26 sentyabrda yenilənib. Müəllif bunu mövsümün ilk mərhələsində müvəqqəti liqa liderliyi kimi təqdim edir; çempionluq deyil.

Rol bölgüsü GK+DEF+MID+FWD+FWD-dır. MID topun arxasında mərkəzi çıxış nöqtəsi saxlayır; hücumçular ayrı kanallarda, fərqli dərinliklərdə dayanır. Müdafiəçinin zərbə vurmasına icazə verilmir. Qərarlar faza → sahiblik → topa müdaxilə → dəstək ardıcıllığında həll edilir. Müəllifin əsas dərsi: düzgün JSON təkbaşına yaxşı futbol demək deyil; identiklik, istiqamət, sahiblik və icra nəticəsi ayrıca yoxlanmalıdır. Daha zəif zərbə gücü sınaqları saxlanmayıb. Yazıda bəzi gözlənilən sahiblik sahələrinin real sorğularda görünmədiyi də açıqlanır.

Bizim nəticəmiz: bu yazını tam köçürülmüş qalib agent kimi göstərmək olmaz. Bizdə `(team, player)` identikliyi və köhnə `possessionAgentId` formatı artıq dəstəklənir; yeni mənbə bu yoxlamaların vacibliyini gücləndirir. MID-in geridə qalması ayrıca gələcək taktika fərziyyəsidir; hazırkı düzülüş müqayisəsinə gizlicə əlavə edilməyib.

## Reddit-də birbaşa yarış iştirakçılarının müzakirəsi

Brauzerdə ümumi Reddit axtarışı CAPTCHA istədi; onu keçmədik. Sonra veb axtarışında indekslənmiş açıq mövzular oxundu.

- [İlk həftə və düzülüşlər](https://www.reddit.com/r/AgenticFootballCup/comments/1wdi3wz/welcome_to_ragenticfootballcup_introduce_yourself/): `Selbeven` 1–2–1, bütün rollarda Nova Lite ilə 8–2 və 38:18 qol nəticəsi bildirir. `mrmg` praktikada 2–0–2-yə yaxın oynadığını, konkret mövqe təlimatları yazdıqda portal düzülüşünü dəyişməyin az fərq etdiyini yazır. Bunlar özlərinin verdiyi hesabatlardır; prompt və matç jurnalı olmadan nəticəni təkrar etmək mümkün deyil. Qapıçının topu öz qapısına aparması, oyunçuların küncə qaçması barədə təkrarlanan şikayətlər var. Şikayətləri təsdiqlənmiş mühərrik xətası kimi qəbul etmirik.
- [AWS Agentic Cup Strategies](https://www.reddit.com/r/AgenticFootballCup/comments/1wegg65/aws_agentic_cup_strategies/): iştirakçılar meydandan kənar topu təqib etməyi və modelin gecikmiş qərarını müzakirə edir. Hazırkı kodda meydan sərhədi, faza yoxlaması və köhnə model sorğularını növbəyə yığmamaq qaydası var.
- [Dördüncü həftə](https://www.reddit.com/r/AgenticFootballCup/comments/1wx1cja/how_was_week_4/): əvvəl üç həftə 9–1 bildirən iştirakçı yeni həftədə nəticəsinin zəiflədiyini yazır. Səbəb kimi mühərrik dəyişməsindən şübhələnir, bunu sübut etmir. Digər iştirakçı sınaq versiyasının avtomatik qəbul dövründə rəqabət matçına düşdüyünü bildirir. Praktik dərs: matçdan əvvəl versiyanı sabitləşdirmək və yoxlanmamış dəyişikliklə rəsmi oyuna girməmək.

## X və sosial paylaşımlar

[Minds by Animoca Brands-in açıq X profili](https://x.com/hellominds_) brauzerdə oxundu. [15 oktyabr paylaşımı](https://x.com/hellominds_/status/2110749276208796145) “Giant Killer” wildcard çağırışıdır; qalib taktikasının açıq kodunu vermir. Profil daxilində axtarış giriş səhifəsinə yönləndirdi. Giriş arxasındakı paylaşımların yoxlandığı iddia edilmir. İndekslənmiş ümumi X axtarışlarında əlavə təsdiqlənə bilən agent kodu tapılmadı; bu, belə kodun heç yerdə olmadığı mənasına gəlmir.

Əvvəlki araşdırmadakı LinkedIn qalib paylaşımları və APJ/EMEA/GCR turnir cədvəlləri qüvvədədir. Turnir nəticəsinin açıq olması agent sisteminin də açıq olması demək deyil. Snow Halation FC və Blitz Cougars-ın tam agentlərini əldə etməmişik və onlara qarşı matç keçirdiyimizi demirik.

## Kaggle: yeni oxunan mənbələr

[Raw Beast — 3-cü yer](https://www.kaggle.com/competitions/google-football/discussion/200709) bu dəfə brauzerdə tam açıldı. Müəlliflər əvvəl güclü təqdimatların davranışını öyrənib, sonra KL məhdudiyyəti ilə RL təlimi aparıblar. Təcrübənin yarısını self-play, yarısını müxtəlif sabit rəqiblərdən ibarət hovuz verib. Sadələşdirilmiş qol/qol-buraxma mükafatı daha mürəkkəb mükafatlardan yaxşı işləyib. Onlar köhnə 2.6 mühərrikində ötürmə problemi üzündən itirilən vaxtı, 2.8-ə keçiddən sonra dəyişən davranışı və tək leaderboard nəticəsinin yüksək dəyişkənliyini vurğulayırlar. Bir neçə güclü agenti qarışdırmaq onların ən güclü tək agentini keçməyib. Bizə dərs: müxtəlif rəqiblərlə, sabit mühərrikdə və yeni toxunulmamış sınaq oyunlarında ölçmək.

[Raw Beast agent dataset-i](https://www.kaggle.com/datasets/dott1718/raw-beast-grf-agents) giriş açıldıqdan sonra endirildi. Hər iki Python faylının mənbə kodu oxundu; çəkilər yüklənib icra edilmədi. `nov_23_WK6_unroll64_deep_r3_cp118.py` və `deep5_SF220_kl2_cp385.py` daxilində çəkiləri çıxmaqla kod eynidir: 64 vahidli ayrıca xüsusiyyət blokları, komanda–rəqib cütlərinin nisbi mövqeləri, yaxın rəqib, son ötürmə/zərbədən keçən vaxt və top uçarkən saxlanan ofsayd məlumatı. Siyasət softmax paylanmasından 19 əmrdən birini seçir. Arxitektura 10 komanda yoldaşı və 11 rəqibə sabitlənib; AWS 5v5 üçün birbaşa uyğun deyil. Faylların SHA-256 izləri `EXTERNAL_CODE_INSPECTION.json`-dadır. Dataset lisenziyası “Unknown” olduğuna görə mənbə faylları təqdimat paketinə köçürülmədi.

[liveinparis — 6-cı yer, açıq kod və çəkilər](https://github.com/seungeunrho/football-paris) ayrıca oxundu. Yoxlanan commit: `20d9ec464edce9153839b66a60dcb02874ea15ee`. README 30 CPU nüvəsi və bir GPU ilə 370 saat təlim bildirir. Kodda topa nisbi vəziyyət, ən yaxın rəqib/komanda yoldaşı, komanda məlumatı blokları, Conv1D+LSTM və ayrı hərəkət başlığı var. Model arxitekturasında 10 komanda yoldaşı və 11 rəqib üçün sabit ölçülər görünür. Buna görə çəkilər bizim 4 komanda yoldaşı/5 rəqib və AWS əmr formatında birbaşa işləmir. Çəkilər icra edilməyib; çempion modelinin bizə köçürüldüyü iddia edilmir.

WeKick və SaltyFish-in istifadəçinin əvvəl göndərdiyi tam yazıları da əvvəlki hesabatda nəzərə alınıb. PPO/IMPALA, minlərlə CPU ilə liqa təlimi və başqa oyun mühərrikinin taktikasını bu gün yerli qaydalarımıza adını dəyişərək əlavə etmək həmin modeli yenidən qurmaq sayılmır.

## Əlavə açıq AWS alətləri

[romina-rodriguez/aws-agentic-fc](https://github.com/romina-rodriguez/aws-agentic-fc/tree/main/agentic-football-sample-agents/ai-team-strands-gateway/gateway_tools) commit `d057412d2b5481e2ceb1690d7c83732650349af6` daxilində ötürmə, zərbə, boş zona və təhlükə sıralama alətləri oxundu. Bunlar faydalı struktur nümunələridir, təsdiqlənmiş qələbə modeli deyil. `evaluate_shot.py`-dakı “success_probability” əl ilə yazılmış düsturdur, real matçlardan kalibrasiya edilmiş ehtimal deyil. Qapı yarımeni 5 qəbul edilir; yerli mühərrikimizdə faktiki yarımen 3.66-dır. Düsturu və rəqəmləri kor-koranə götürmədik. Əlavə Gateway/Memory şəbəkə çağırışlarının vaxt xərci də bizim şəraitdə ölçülməyib.

Repo Windows-da çox uzun, mövzuya aid olmayan bir neçə fayl yolu səbəbindən tam checkout edilmədi. Yuxarıda göstərilən futbol alət faylları yerli checkout-da mövcud idi və məhz onlar oxundu. Heç bir deploy və xarici bulud dəyişikliyi edilmədi.

## İnsan futzalından götürülən, sınağa çevrilən fikirlər

Buradakı rəqəmlər **qapıçını saymır**: bütün sxemlərdə bir GK və cəmi dörd meydan oyunçusu var. Futzal ilə AWS/AgentPitch-in ofsayd, fizika və qərar tezliyi eyni deyil.

- [FIFA: Opposed build-up](https://www.fifatrainingcentre.com/en/game/tournaments/fifa-futsal-world-cup/opposed-build-up.php): komandaların çoxu ən azı iki sistemdən istifadə edib. 3–1 pivotla irəliləməni, 4–0 rəqibi çıxarıb arxasında boşluq tapmağı dəstəkləyir. Tək arxa oyunçuya press edilərkən digər oyunçuların çox uzaqda qalması təhlükəlidir.
- [FIFA: 3–1-də pivotun rolu](https://www.fifatrainingcentre.com/en/practice/futsal/block-5/3-1-system-role-of-the-pivot.php): pivot hücuma dərinlik verir; topu saxlayıb tərəfdaşla birləşir və ya dönüb zərbə vurur. Ən arxadakı oyunçu əks-hücumu örtməlidir.
- [FIFA: 4–0-da boşluq yaratmaq](https://www.fifatrainingcentre.com/en/practice/futsal/block-5/4-0-system-creating-space-in-behind.php): paralel/diaqonal ötürmə xətləri, top ətrafında üçbucaq və tərəfdaşın zonasını doldurmamaq. Bizim 4–0 namizədimiz bu ideyalardan götürülmüş sadələşdirilmiş mobil dəstək variantıdır; peşəkar futzalın bütün rotasiya kombinasiyalarının tam modeli deyil.

## Sınaqda konkret nə dəyişdi?

Əvvəlki V3 nəzarət variantına əlavə səkkiz mobil dəstək quruluşu yazıldı: **1–1–2, 1–2–1, 2–1–1, 2–2, 1–1–1–1, 3–1, 1–3, 4–0**. 2–2, Reddit-də yazılan 2–0–2 ilə eyni dörd meydan oyunçusunu bildirir.

Ötürmə seçimi, 30 m zərbə həddi, zərbə gücü, meydan, fizika, atributlar, ilk düzülüşün roster rolları və rəqiblər dəyişdirilmədi. Dəstək nöqtələri və 4–0 üçün hərəkətli arxa örtük dəyişdi. Top sahibi olduğu anda hərəkət, tək pressçi və müdafiədə fərdi örtük ümumi qaydalardır; onlar dəstək nöqtəsindən əvvəl gələ bilər. Bu, portalın yalnız “formation” seçicisinin təsirini ölçən sınaq deyil. Eyni başlayan komandanın faktiki mövqelənmə siyasətlərini ölçür.

İlk nəzarət yoxlamasında yeni kodun `original` variantı ilə arxiv V3-ün hər iki tərəfdə **bütün native matç hadisələri eyni** alındı. Sonra toxunulmamış oyun toxumları üzrə seçim, ayrıca doğrulama və yekun sınaq ayrıldı. Nəticələr və seçimin qərarı ayrıca nəticə hesabatında verilir.
