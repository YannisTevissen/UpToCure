from smolagents_repo.examples.open_deep_research.run import deep_research_agent


def main():
    disease = "Spinal Muscular Atrophy"
    prompt = f"""Develop a comprehensive and exhaustive review of all recent research efforts aimed at curing {disease}. Your review should:
    
	•	Scope the Research: Gather data from the latest peer-reviewed articles, clinical trials, preclinical studies, and innovative experimental therapies related to {disease}.
	•	Detail Key Aspects: Identify and explain major breakthroughs, emerging trends, methodologies, funding sources, and the leading institutions driving these research efforts.
	•	Critical Analysis: Evaluate the strengths and limitations of each approach and discuss the challenges that remain in the path toward a cure.
	•	Popularize the Content: Translate complex scientific details into accessible language that is understandable for a broad audience while preserving technical accuracy for expert readers.
	•	Provide Citations: Include comprehensive citations and direct links to all original sources and research articles to ensure transparency and ease of further exploration.
    •	Answer in markdown format and cite your sources.
    •	Don't forget to search for new research directions, even if they are early.
    •	Use the following format:
    # {disease}
    report
    
    Answer in markdown format and cite your sources."""
    output = deep_research_agent(prompt=prompt)
    print(output)
    with open(f"../UpToCure/reports/{disease}.md", "w") as f:
        f.write(output)
