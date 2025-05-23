from datetime import datetime, timedelta


######################## FUNCTIONS


def get_usage_data(days_ago):
    """
    Generate usage data payload for Azure Cost Management API.

    Args:
        days_ago (int): Number of days ago to calculate the usage data for.

    Returns:
        dict: The usage data payload.
    """
    return {
        'type': 'Usage',
        'timeframe': 'Custom',
        'timePeriod': {
            'from': (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT00:00:00Z'),
            'to': (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT23:59:59Z')
        },
         'dataset': {
            "filter": {
                "or": [
                    {
                        "dimensions": {
                            "name": "ServiceName",
                            "operator": "In",
                            "values": [
                                "Virtual Machines",
                                "SQL Database",
                                "Azure App Service",
                                "Bandwidth",
                                "Storage",
                                "Log Analytics"
                            ]
                        }
                    },
                    {
                    "tags": {
                        "name": "app",
                        "operator": "In",
                        "values": [
                            "mongodb"
                        ]
                    }
                    }
                ]
            },
            'granularity': 'Daily',
            'aggregation': {
                'totalCost': {
                    'name': 'Cost',
                    'function': 'Sum'
                }
            },
            'grouping': [
                {
                    'type': 'Dimension',
                    'name': 'ServiceName'
                }
            ]
        }
    }


def extract_cost_data(response):
    """
    Extract cost data from the Azure API response.

    Args:
        response (requests.Response): The response object from the Azure API.

    Returns:
        list: A list of cost data rows.

    Raises:
        KeyError: If the response JSON does not contain the expected structure.
    """
    if (
        isinstance(response.json(), dict)
        and 'properties' in response.json()
        and isinstance(response.json()['properties'], dict)
        and 'rows' in response.json()['properties']
    ):
        return response.json()['properties']['rows']
    else:
        print("Unexpected response structure:")
        print(json.dumps(response.json(), indent=2))
        raise KeyError("Response JSON does not contain 'properties' or 'rows' as expected.")

def process_cost_data(usage_response):
    """
    Process the cost data from the Azure API response.

    Args:
        usage_response (requests.Response): The response object from the Azure API.

    Returns:
        list: A list of dictionaries containing cost data.
    """
    # Extract the cost data using the function
    cost_data = extract_cost_data(usage_response)

    # Convert the list of lists to a list of dictionaries
    cost_data = [
        {
            'cost': row[0],
            'date': row[1],
            'service': row[2],
            'currency': row[3]
        }
        for row in cost_data
    ]

    return cost_data

def calculate_and_display_costs(cost_data):
    """
    Calculate total costs, sort services by cost, and display the results.

    Args:
        cost_data (list): A list of dictionaries containing cost data for a time period.

    Returns:
        dict: A dictionary containing total cost, total cost date, and top services by cost.
    """
    # Calculate the total cost and the date of the total cost
    total_cost = 0
    total_cost_date = None
    total_cost_date_1 = "N/A"  # Initialize with a default value
    for row in cost_data:
        if total_cost_date is None or row['date'] > total_cost_date:
            total_cost_date = row['date']
            date_obj = datetime.strptime(str(total_cost_date), "%Y%m%d")
            total_cost_date_1 = date_obj.strftime("%Y-%m-%d")
        total_cost += row['cost']

    total_cost_brls = total_cost

    # Sort the list of dictionaries by cost in descending order
    cost_data_sorted = sorted(cost_data, key=lambda k: k['cost'], reverse=True)

    # Print the total cost and its date
    if os.getenv('DEBUG', 'false').lower() == 'true':
        print(f'Total cost on {total_cost_date_1}: {total_cost_brls} {cost_data[0]["currency"]}')

    # Print the top 5 services by cost

    if os.getenv('DEBUG', 'false').lower() == 'true':
        print('Top 5 services by cost:')
        for i, row in enumerate(cost_data_sorted):
            print(f"{i+1}. ServiceName: {row['service']} - R${row['cost']} {row['currency']}")

    # Review
    list_items = [f"<li> ServiceName: {row['service']} - R${row['cost']} {row['currency']}</li>" for row in cost_data_sorted]
    if os.getenv('DEBUG', 'false').lower() == 'true':
        print(f'check: {list_items}')

    return {
        "total_cost": total_cost_brls,
        "total_cost_date": total_cost_date_1,
        "top_services": cost_data_sorted[:7]
    }

def compare_service_costs(cost_data_a, cost_data_b, label_a, label_b, highlight_threshold=10):
    """
    Compare two lists of service cost data and print a table with cost, difference, and percentage change.
    Highlight significant changes (>highlight_threshold% increase).
    Also returns a list of HTML rows for email reporting, sorted by absolute Diff (%).

    Args:
        cost_data_a (list): List of dicts for the first period.
        cost_data_b (list): List of dicts for the second period.
        label_a (str): Label for the first period.
        label_b (str): Label for the second period.
        highlight_threshold (float): Percentage threshold for highlighting increases.

    Returns:
        str: HTML table rows for email body.
    """


    a_dict = {row['service']: row['cost'] for row in cost_data_a}
    b_dict = {row['service']: row['cost'] for row in cost_data_b}
    all_services = set(a_dict) | set(b_dict)

    # Prepare all rows with calculated values
    rows = []
    for service in all_services:
        cost_a = a_dict.get(service, 0)
        cost_b = b_dict.get(service, 0)
        diff = cost_a - cost_b
        try:
            percent = (diff / cost_b * 100) if cost_b else float('inf') if cost_a else 0
        except ZeroDivisionError:
            percent = float('inf')
        rows.append({
            "service": service,
            "cost_a": cost_a,
            "cost_b": cost_b,
            "diff": diff,
            "percent": percent
        })

    # Sort rows by absolute value of percent difference, descending
    rows.sort(key=lambda x: abs(x["diff"]), reverse=True)

    print(f"\n{'Service':<25} | {label_a:<15} | {label_b:<15} | Diff (R$)     | Diff (%)")
    print("-" * 80)

    html_rows = []
    for row in rows:
        highlight = row["percent"] > highlight_threshold
        marker = "**" if highlight else "  "
        row_str = (
            f"{marker} "
            f"{row['service']:<25} | "
            f"R${row['cost_a']:<13.2f} | "
            f"R${row['cost_b']:<13.2f} | "
            f"R${row['diff']:<11.2f} | "
            f"{row['percent']:>7.2f}%"
        )
        print(row_str)

        html_row = (
            f"<tr style='background-color:#ffcccc;'>" if highlight else "<tr>"
        )
        html_row += (
            f"<td>{row['service']}</td>"
            f"<td>R${row['cost_a']:,.2f}</td>"
            f"<td>R${row['cost_b']:,.2f}</td>"
            f"<td>R${row['diff']:,.2f}</td>"
            f"<td>{row['percent']:.2f}%</td>"
            "</tr>"
        )
        html_rows.append(html_row)
    return "\n".join(html_rows)

######################## END OF FUNCTIONS
