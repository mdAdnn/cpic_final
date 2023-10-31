import psycopg2
import datetime

# Your database connection parameters
db_params = {
    "database": "postgres",
    "user": "postgres",
    "password": "adnan",
    "host": "localhost",
    "port": "5432"
}

# Read input values from input.txt and organize them into a list of dictionaries
with open('C:/Users/fcbwa/OneDrive/Desktop/cpic_final-1/input_values_2.txt', 'r') as file:
    lines = file.readlines()
    
    # Initialize variables
    input_data = []
    entry = {}  # Initialize an empty dictionary for the entry

    for line in lines:
        line = line.strip()
        if line.startswith("name:"):
            # If a new entry begins, save the previous one (if any)
            if entry:
                input_data.append(entry)
            entry = {"name": line.replace("name: ", "")}  # Initialize a new entry with the name
        elif line.startswith("id:"):
            entry["id"] = line.replace("id: ", "")  # Add the ID to the current entry
        elif line:
            # Assuming any non-empty line is genesymbol,diplotype
            genesymbol, diplotype = line.split(",")
            entry[genesymbol] = diplotype

    # Append the last entry (if any)
    if entry:
        input_data.append(entry)

# Get current timestamp
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Initialize HTML content
html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Pharmacogenomic Report</title>
    </head>
    <body style="background-color: #fdfdfd;">
        <div style="background-color: #4CAF50; padding: 20px; box-shadow: 5px 5px 5px #888888; display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; flex-direction: column;">
                <h1 style="font-family: Arial, sans-serif; font-size: 36px; font-weight: bold; color: #fff; text-shadow: 2px 2px #888888, 2px 2px 5px #888888; margin: 0;">Pharmacogenomic Report</h1>
                <br>
            </div>
            <img src="https://www.hbku.edu.qa/sites/default/files/media/images/hbku_2021.svg" alt="Hamad Bin Khalifa University" title="Hamad Bin Khalifa University" style="height: 100px; margin-left: 20px;">
        </div>
"""

# Create a dictionary to store the results for each gene
gene_results = {}

# Your existing database connection and query execution code

# Connect to the database
conn = psycopg2.connect(**db_params)

# Create a cursor
cursor = conn.cursor()

# Loop through the entries and generate and execute SQL queries for each gene
for entry in input_data:
    print("Processing entry:")
    print(entry)  # Print the entire entry for debugging
    name = entry["name"]
    id = entry["id"]

    for genesymbol, diplotype in entry.items():
        if genesymbol not in ("name", "id"):
            print(f"Gene Symbol: {genesymbol}")
            print(f"Diplotype: {diplotype}")
            print("-----------------")  # Separator between entries

            # Construct your SQL query and execute it
            sql_query = f"""
                SELECT DISTINCT ON (p.drugid)
                    dp.*,
                    p.drugid,
                    dr.name,
                    r.drugrecommendation,
                    r.classification
                FROM cpic.gene_result_diplotype d
                JOIN cpic.gene_result_lookup l ON d.functionphenotypeid = l.id
                JOIN cpic.gene_result gr ON l.phenotypeid = gr.id
                JOIN cpic.pair p ON gr.genesymbol = p.genesymbol
                JOIN cpic.drug dr ON p.drugid = dr.drugid
                JOIN cpic.recommendation r ON dr.drugid = r.drugid
                JOIN cpic.diplotype_phenotype dp ON r.phenotypes = dp.phenotype
                WHERE dp.diplotype ->> '{genesymbol}' = '{diplotype}'
                AND r.classification <> 'No Recommendation'
                AND r.drugrecommendation <> 'No recommendation'
                ORDER BY p.drugid, r.classification;
                """
            cursor.execute(sql_query)
            results = cursor.fetchall()

            # Store the results for this gene in the dictionary
            gene_results[f'{genesymbol} - {diplotype}'] = results

# Create a list to store gene symbols as links
gene_links = []

# Add gene symbols as clickable links and create anchor points
for gene in gene_results.keys():
    gene_link = f"<a href='#results_{gene}'>{gene}</a>"
    gene_links.append(gene_link)

# Add the summary section to the HTML content
html_content += f"<p style='margin-bottom: 5px;'><b>Name: </b>{name}</p>"
html_content += f"<p style='margin-bottom: 5px;'><b>ID: </b>{id}</p>"
html_content += f"<p style='margin-bottom: 5px;'><b>Time: </b>{timestamp}</p>"
html_content += "<h3>Queried Genes</h3>"

# Add the list of gene links at the beginning of the introduction section
for gene_link in gene_links:
    html_content += f"<li>{gene_link}</li>"
html_content += "</ul>"

# Initialize a flag to check if any result has a "Strong" classification
strong_classification_found = False

# Initialize a list to store genes with "Strong" classification
strong_genes = []

# Loop through the gene results and add them to the HTML content
for gene, results in gene_results.items():
    if results:
        # Check if the classification is "Strong"
        strong_classification_in_gene = any(row[7] == "Strong" for row in results)

        html_content += f"<a name='results_{gene}'></a>"
        html_content += f"<div style='margin-top: 10px;'>"  # Add styling to create space
        html_content += f"<h4>{gene}</h4>"
        html_content += f"<p>Total Results: {len(results)}</p>"
        
        if strong_classification_in_gene:
            strong_classification_found = True
            strong_genes.append(gene)

        html_content += "<table style='border-collapse: collapse; border: 1px solid black;'>"
        html_content += """
            <tr>
                <th style='border: 1px solid black;'>Diplotype</th>
                <th style='border: 1px solid black;'>Activity Score</th>
                <th style='border: 1px solid black;'>Phenotype</th>
                <th style='border: 1px solid black;'>EHR Priority</th>
                <th style='border: 1px solid black;'>Drug ID</th>
                <th style='border: 1px solid black;'>Drug Name</th>
                <th style='border: 1px solid black;'>Recommendation</th>
                <th style='border: 1px solid black;'>Classification</th>
            </tr>
        """

        for row in results:
            html_content += f"""
            <tr>
                <td style='border: 1px solid black;'>{row[0]}</td>
                <td style='border: 1px solid black;'>{row[1]}</td>
                <td style='border: 1px solid black;'>{row[2]}</td>
                <td style='border: 1px solid black;'>{row[3]}</td>
                <td style='border: 1px solid black;'>{row[4]}</td>
                <td style='border: 1px solid black;'>{row[5]}</td>
                <td style='border: 1px solid black;'>{row[6]}</td>
                <td style='border: 1px solid black;'>{row[7]}</td>
            </tr>
            """
            
        html_content += "</table>"
               

# If strong_classification_found is True, add the "Results" section
if strong_classification_found:
    total_genes_queried = len(gene_results)  # Get the total number of genes queried
    html_content += "<h2>Results</h2>"
    html_content += f"<p>The total number of genes queried were: {total_genes_queried}</p>"
    html_content += "<p>Genes with 'Strong' classification:</p>"
    html_content += "<ul>"  # Create an unordered list
    for gene in strong_genes:
        html_content += f"<li>{gene}</li>"  # Add each strong gene to the list
    html_content += "</ul>"
else:
    html_content += "<h2>Results</h2>"
    html_content += "<p>No Strong classification were found.</p>"

# Calculate the total results for all entries
total_results = sum(len(results) for results in gene_results.values())

# Add the total results for all entries to the summary section
html_content += "<h4 style='font-size: 18px; line-height: 1.5;'><b>Summary</b></h4>"
html_content += f"<p style='font-size: 16px; line-height: 1.5;'>Total Results for All Entries: {total_results}</p>"
html_content += "<h5 style='font-size: 12px; line-height: 1;'><b>Methodology</b></h5>"
html_content += f"<p style='font-size: 12px; line-height: 1;'>Genotypes were called using Aldy version 2.0.0. Actionable drug recommendations were obtained from CPIC guidelines.</p>"

# Complete HTML content
html_content += """
</body>
</html>
"""

# Write HTML content to a file
with open("pharmacogenomic_report_2.html", "w") as html_file:
    html_file.write(html_content)

# Close the cursor and connection
cursor.close()
conn.close()

print("Pharmacogenomic Report generated.")
