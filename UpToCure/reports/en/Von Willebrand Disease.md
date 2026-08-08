---
title: Von Willebrand Disease
date: '2026-08-08'
model: gpt-5.6-terra
backend: openai-responses
generator: uptocure-reports-generator
summary: Recent research efforts aimed at curing Von Willebrand Disease.
input_tokens: 80352
output_tokens: 5442
search_calls: 10
cost_usd: 0.326
---

# Von Willebrand Disease

## Overview

Von Willebrand disease (VWD) is an inherited bleeding disorder caused by too little von Willebrand factor (VWF), or by VWF that does not work properly. VWF helps platelets form an initial plug at an injury site and protects clotting factor VIII in the bloodstream; therefore, VWD can cause nosebleeds, easy bruising, prolonged bleeding after dental work or surgery, heavy menstrual bleeding, and—particularly in severe type 3 disease—serious internal bleeding. Types 1 and 3 primarily reflect low or absent VWF, whereas type 2 includes several forms in which VWF is present but dysfunctional. Severity and prognosis vary widely: many people have mild symptoms, while a smaller group requires regular preventive treatment. [ASH/ISTH/NHF/WFH diagnostic guideline](https://pmc.ncbi.nlm.nih.gov/articles/PMC7805340/)

Current care prevents or treats bleeding rather than correcting the inherited VWF defect. Depending on VWD subtype and clinical setting, standard care includes desmopressin to release a person’s own stored VWF, tranexamic acid to slow clot breakdown, and intravenous plasma-derived or recombinant VWF concentrates; people with frequent severe bleeds may receive regular VWF-concentrate prophylaxis. [ASH/ISTH/NHF/WFH management guideline](https://ashpublications.org/bloodadvances/article/5/1/301/474884/ASH-ISTH-NHF-WFH-2021-guidelines-on-the-management)

## Scope of Recent Research (2020–present)

Research aimed at a cure has become more technically sophisticated but remains early-stage: the main questions are how to deliver a very large VWF gene or gene-editing machinery specifically to endothelial cells—the blood-vessel lining cells that naturally produce VWF—and how to address the many different disease-causing variants. The field’s most meaningful curative-direction advances are allele-selective RNA silencing and CRISPR-based removal of a harmful VWF copy in dominant-negative type 2 disease, alongside endothelial-targeted gene-replacement studies; however, no gene or cell therapy for VWD has entered clinical trials, so a durable cure is not yet close to routine care. [Gene therapy and genome editing review](https://www.frontiersin.org/journals/genome-editing/articles/10.3389/fgeed.2025.1620438/full)

## Major Breakthroughs and Emerging Therapies

**Endothelial-targeted gene replacement.** A major obstacle is that the VWF coding sequence is about 8.4 kilobases—too large for one standard adeno-associated virus (AAV) vector—and that VWF made outside its normal endothelial-cell setting may not function optimally. In a 2023 proof-of-principle study, investigators split VWF across two engineered AAV9 vectors, used an endothelial-specific promoter and an endothelial-targeting capsid peptide, and achieved stable VWF expression after systemic administration in VWF-deficient mice. The amount produced was still below therapeutic levels and did not restore factor VIII activity, so this was an important platform advance rather than a functional cure. [Dual hybrid endothelial AAV-VWF study](https://www.nature.com/articles/s41434-020-00218-6)

**Allele-selective RNA therapeutics.** For some type 2 forms of VWD, a mutant VWF protein interferes with the healthy protein made from the other gene copy; this is called a dominant-negative effect. Researchers have developed small interfering RNAs (siRNAs), short RNA molecules that instruct cells to destroy a selected messenger RNA, aimed at a harmless single-letter DNA difference linked to the mutant VWF copy rather than the disease mutation itself. In endothelial cells and mouse models, lipid nanoparticles delivered these siRNAs to the endothelium and selectively reduced the targeted VWF allele, establishing the principle that mutant VWF can be lowered without eliminating the healthy allele. [siRNA allele-selective silencing study](https://pmc.ncbi.nlm.nih.gov/articles/PMC10582391/)

The strongest disease-model evidence so far came from a 2025 study of heterozygous type 2B VWD mice. Endothelial-targeted lipid nanoparticles carrying an allele-selective siRNA preferentially reduced mutant VWF, improved the VWF multimer pattern and collagen-binding activity, reduced platelet aggregates, and normalized tail-bleeding time in four of six treated mice. Because siRNA effects fade and require repeat dosing, this approach could become a highly targeted treatment but would not be a permanent genetic cure. [Type 2B siRNA correction in mice](https://pmc.ncbi.nlm.nih.gov/articles/PMC11786658/)

**CRISPR-based allele-selective disruption and precision modeling.** A 2026 ex vivo study used CRISPR-Cas9 in patient-derived endothelial colony-forming cells (ECFCs) from people with type 2A and type 2B VWD. Rather than designing a separate editor for every disease mutation, the team targeted the common VWF single-nucleotide polymorphism rs1800378 to selectively disable the mutant allele while preserving VWF expression from the untargeted healthy allele; this reduced mutant protein and reversed cellular disease features. This is a notable potential route toward a one-time cure for selected dominant-negative forms, but it has not yet been tested as an in-body treatment or in people. [CRISPR allele-selective VWF disruption](https://pubmed.ncbi.nlm.nih.gov/41411488/)

Researchers are also using base editing—single-letter DNA conversion without a conventional double-strand DNA break—to build more faithful patient models and identify which defects would need correction. In 2025, investigators introduced the severe p.M771V VWF variant into normal cord-blood ECFCs, showing that it causes VWF retention in the endoplasmic reticulum, defective processing, reduced secretion, and loss of high-molecular-weight VWF multimers. Such models do not cure disease themselves, but they enable testing of tailored editing, RNA, and protein-rescue strategies in the relevant cell type. [p.M771V endothelial base-editing model](https://www.sciencedirect.com/science/article/pii/S1538783624006391)

## Clinical Trials and Experimental Approaches

No registered clinical trial is currently testing gene replacement, gene editing, or cell therapy as a cure for VWD. The leading human studies instead seek longer-lasting prevention of bleeding. Hemab Therapeutics’ VELORA Pioneer study of HMB-002 is an open-label Phase 1/2 trial that began on February 6, 2025, plans to enroll 108 adults with type 1, type 1C, or type 2A VWD, and is designed to assess single and repeat subcutaneous doses through an estimated July 2027 completion. HMB-002 is an antibody intended to stabilize a person’s endogenous VWF and thereby raise VWF and factor VIII levels; it is not gene therapy and cannot correct a pathogenic VWF variant. [VELORA Pioneer trial record](https://clinicaltrials.gov/study/NCT06754852) [HMB-002 development program](https://www.hemab.com/news-items/hemab-therapeutics-announces-157-million-series-c-financing-to-advance-next-generation-treatments-for-underserved-bleeding-disorders)

VGA039, also called latarcibart, is a subcutaneous antibody that targets protein S to increase thrombin generation—the biochemical process that produces a stable clot—without replacing or repairing VWF. Its ongoing VIVID Phase 1/2 master protocol, sponsored by Vega Therapeutics, includes healthy-volunteer, single-dose, multidose, surgical-prophylaxis, and extension components; as listed in the registry, results have not been posted. [VIVID Phase 1/2 trial record](https://clinicaltrials.gov/study/NCT05776069) A separate Phase 3 study, VIVID-6, began on October 15, 2025, with planned enrollment of 60 adolescents and adults across VWD types and an estimated completion in October 2028. [VIVID-6 Phase 3 trial record](https://clinicaltrials.gov/study/NCT07115004)

## Methodologies and Scientific Approaches

The cure-directed research pipeline relies on patient-derived ECFCs, which can be isolated from peripheral blood and preserve many endothelial features relevant to VWF synthesis, storage in Weibel-Palade bodies, secretion, multimer formation, and factor VIII binding. Investigators compare these cells with engineered ECFCs, standard cell lines, and VWD mouse models, measuring VWF antigen and activity, factor VIII activity, VWF multimer distribution, intracellular trafficking, platelet-related phenotypes, and bleeding time. [ECFCs as VWD research models](https://pubmed.ncbi.nlm.nih.gov/39243860/) [p.M771V endothelial base-editing model](https://www.sciencedirect.com/science/article/pii/S1538783624006391)

Delivery technology is the central bottleneck. Gene-addition programs are testing dual-AAV systems to fit the oversized VWF sequence, whereas RNA and editing programs are investigating endothelial-directed lipid nanoparticles, transient editor delivery, and allele-specific guide or siRNA design. Researchers increasingly use common linked single-nucleotide polymorphisms as targets, because this may allow one treatment design to address multiple pathogenic variants while sparing the healthy VWF allele. [Gene therapy and genome editing review](https://www.frontiersin.org/journals/genome-editing/articles/10.3389/fgeed.2025.1620438/full) [CRISPR allele-selective VWF disruption](https://pubmed.ncbi.nlm.nih.gov/41411488/)

## Leading Institutions and Funding

Much of the cure-oriented work is concentrated in the Netherlands. Erasmus University Medical Center, Amsterdam UMC, Sanquin Research and Landsteiner Laboratory, and Leiden University Medical Center collaborated on the recent CRISPR, ECFC, and VWF biology studies; the p.M771V program used samples from the Willebrand in the Netherlands cohort. [p.M771V endothelial base-editing model](https://www.sciencedirect.com/science/article/pii/S1538783624006391) [CRISPR allele-selective VWF disruption](https://pubmed.ncbi.nlm.nih.gov/41411488/) The Netherlands Organization for Scientific Research, through its Applied and Engineering Sciences “Connecting Innovators” Open Technology Programme project 18712, supports this gene-therapy and editing research stream. [Gene therapy and genome editing review](https://www.frontiersin.org/journals/genome-editing/articles/10.3389/fgeed.2025.1620438/full)

On the clinical innovation side, Hemab Therapeutics is developing HMB-002 and raised a $157 million Series C financing round in October 2025 to advance its broader bleeding-disorder pipeline, including HMB-002 toward registration studies. [Hemab Series C financing](https://www.hemab.com/news-items/hemab-therapeutics-announces-157-million-series-c-financing-to-advance-next-generation-treatments-for-underserved-bleeding-disorders) Vega Therapeutics sponsors the VGA039 clinical program, while the Dutch Hemophilia Foundation, CSL Behring, the Dutch Thrombosis Foundation, and NWO have supported related VWD cohorts and allele-selective silencing research programs. [Allele-selective VWF silencing in mice](https://pubmed.ncbi.nlm.nih.gov/38461614/)

## Strengths, Limitations, and Challenges

The major strength of recent work is that it targets disease biology rather than simply replacing clotting protein during a bleed. Allele-selective silencing and CRISPR disruption are especially attractive for dominant-negative type 2 VWD because reducing mutant VWF can allow the normal protein from the other allele to form more functional multimers. The use of endothelial cells and endothelial-targeted delivery is also biologically appropriate, since these cells are the natural source of circulating VWF. [Type 2B siRNA correction in mice](https://pmc.ncbi.nlm.nih.gov/articles/PMC11786658/) [CRISPR allele-selective VWF disruption](https://pubmed.ncbi.nlm.nih.gov/41411488/)

The limitations are substantial. VWD includes hundreds of variants and multiple disease mechanisms, meaning that a strategy suited to a dominant-negative type 2 mutation may not help people with type 3 disease, two nonfunctioning copies, or mutations that cause simple VWF loss. AAV delivery is constrained by VWF’s size; editing must reach enough endothelial cells throughout the body; permanent editors create off-target and long-term safety concerns; and siRNA requires repeated administration. Even successful therapies may be expensive, personalized, and difficult to manufacture or distribute equitably. [Dual hybrid endothelial AAV-VWF study](https://www.nature.com/articles/s41434-020-00218-6) [Gene therapy and genome editing review](https://www.frontiersin.org/journals/genome-editing/articles/10.3389/fgeed.2025.1620438/full)

## Outlook and Future Directions

As of August 8, 2026, VWD has no clinical-stage curative gene or cell therapy. The most important milestones to watch are demonstration that endothelial-targeted RNA or editing delivery is safe and durable in large-animal models; replication of allele-selective correction across more VWD mutations and subtypes; restoration of clinically meaningful VWF activity, multimer structure, factor VIII protection, and bleeding control; and eventual first-in-human trials of a genetic approach. In the nearer term, HMB-002 and VGA039 may improve preventive care and reduce treatment burden, but they should be viewed as potentially transformative management therapies rather than cures. [Gene therapy and genome editing review](https://www.frontiersin.org/journals/genome-editing/articles/10.3389/fgeed.2025.1620438/full) [VELORA Pioneer trial record](https://clinicaltrials.gov/study/NCT06754852) [VIVID-6 Phase 3 trial record](https://clinicaltrials.gov/study/NCT07115004)

## References

- [ASH/ISTH/NHF/WFH diagnostic guideline](https://pmc.ncbi.nlm.nih.gov/articles/PMC7805340/) — American Society of Hematology, International Society on Thrombosis and Haemostasis, National Hemophilia Foundation, and World Federation of Hemophilia, 2021.
- [ASH/ISTH/NHF/WFH management guideline](https://ashpublications.org/bloodadvances/article/5/1/301/474884/ASH-ISTH-NHF-WFH-2021-guidelines-on-the-management) — American Society of Hematology, International Society on Thrombosis and Haemostasis, National Hemophilia Foundation, and World Federation of Hemophilia, 2021.
- [Gene therapy and genome editing review](https://www.frontiersin.org/journals/genome-editing/articles/10.3389/fgeed.2025.1620438/full) — Barraclough et al., 2025.
- [Dual hybrid endothelial AAV-VWF study](https://www.nature.com/articles/s41434-020-00218-6) — De Meyer et al., *Gene Therapy*, 2023.
- [siRNA allele-selective silencing study](https://pmc.ncbi.nlm.nih.gov/articles/PMC10582391/) — Jongejan et al., *Blood Advances*, 2023.
- [Type 2B siRNA correction in mice](https://pmc.ncbi.nlm.nih.gov/articles/PMC11786658/) — Linthorst et al., *Blood Advances*, 2025.
- [CRISPR allele-selective VWF disruption](https://pubmed.ncbi.nlm.nih.gov/41411488/) — Bär et al., *Blood Advances*, 2026.
- [p.M771V endothelial base-editing model](https://www.sciencedirect.com/science/article/pii/S1538783624006391) — Bär et al., *Journal of Thrombosis and Haemostasis*, 2025.
- [VELORA Pioneer trial record](https://clinicaltrials.gov/study/NCT06754852) — ClinicalTrials.gov, 2026.
- [HMB-002 development program](https://www.hemab.com/news-items/hemab-therapeutics-announces-157-million-series-c-financing-to-advance-next-generation-treatments-for-underserved-bleeding-disorders) — Hemab Therapeutics, 2025.
- [VIVID Phase 1/2 trial record](https://clinicaltrials.gov/study/NCT05776069) — ClinicalTrials.gov, 2025.
- [VIVID-6 Phase 3 trial record](https://clinicaltrials.gov/study/NCT07115004) — ClinicalTrials.gov, 2026.
- [ECFCs as VWD research models](https://pubmed.ncbi.nlm.nih.gov/39243860/) — Laan et al., *Journal of Thrombosis and Haemostasis*, 2024.
- [Hemab Series C financing](https://www.hemab.com/news-items/hemab-therapeutics-announces-157-million-series-c-financing-to-advance-next-generation-treatments-for-underserved-bleeding-disorders) — Hemab Therapeutics, 2025.
- [Allele-selective VWF silencing in mice](https://pubmed.ncbi.nlm.nih.gov/38461614/) — Jongejan et al., *Thrombosis Research*, 2024.
