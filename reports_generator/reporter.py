from smolagents_repo.examples.open_deep_research.run import deep_research_agent
from datetime import datetime

def generate_report(disease: str):

    prompt = f"""Today is {datetime.now().strftime("%Y-%m-%d")}. Develop a comprehensive and exhaustive review of all recent research efforts aimed at curing {disease}. Your review should:
    
	•	Scope the Research: Gather data from the latest peer-reviewed articles, clinical trials, preclinical studies, and innovative experimental therapies related to {disease}.
	•	Don't forget to search for new research directions, even if they are early.
	•	Detail Key Aspects: Identify and explain major breakthroughs, emerging trends, methodologies, funding sources, and the leading institutions driving these research efforts.
	•	Critical Analysis: Evaluate the strengths and limitations of each approach and discuss the challenges that remain in the path toward a cure.
	•	Popularize the Content: Translate complex scientific details into accessible language that is understandable for a broad audience while preserving technical accuracy for expert readers.
	•	Provide Citations: Include comprehensive citations and direct links to all original sources and research articles to ensure transparency and ease of further exploration. Link relevant sources in markdown [title](link).
    •	Answer in markdown format and cite your sources. Don't use too many bullet points, only when needed write paragraphs and titles up to four #. Don't use tables or images.
    •	Start with:
    # {disease}

    """
    output = deep_research_agent(prompt=prompt)
    print(output)
    with open(f"../UpToCure/reports/{disease}.md", "w") as f:
        f.write(output)

def main():
    rare_diseases_france = [
		"Neurofibromatosis Type 1",
		"Cystic Fibrosis",
		"Hereditary Hemorrhagic Telangiectasia",
		"Prader-Willi Syndrome",
		"Duchenne Muscular Dystrophy",
		"Sickle Cell Disease",
		"Myofasciitis à Macrophages",
		"Mucopolysaccharidosis Type I (Hurler Syndrome)",
		"Fabry Disease",
		"Primary Ciliary Dyskinesia",
		"Hemophilia",
		"Amyotrophic Lateral Sclerosis",
		"Progressive Supranuclear Palsy",
		"Leukodystrophies",
		"Fibrodysplasia Ossificans Progressiva",
		"Progeria",
		"Lysosomal Storage Diseases",
        "Friedreich's Ataxia",
        "Gaucher Disease",
        "Phenylketonuria"
    ]
    for disease in rare_diseases_france:
        generate_report(disease)
