-- Overall Channel Volume & Value
-- Which sourcing channel recruits the most agents, and which brings in the most total premium?

SELECT 
    a.Sourcing_Channel,
    COUNT(DISTINCT a.Agent_ID) AS Total_Agents_Recruited,
    COUNT(p.Policy_ID) AS Total_Policies_Sold,
    SUM(CAST(p.Premium_Amount AS BIGINT)) AS Total_Premium_Generated
FROM dbo.agents a
LEFT JOIN dbo.policies p ON a.Agent_ID = p.Agent_ID
GROUP BY a.Sourcing_Channel
ORDER BY Total_Premium_Generated DESC;

-- Sourcing ROI (Return on Investment)
-- The Business Question: We spend different amounts recruiting on LinkedIn vs. Job Portals.
-- Which channel gives us the highest premium return per rupee spent on recruitment?
-- What it proves: Creating calculated columns and understanding business profitability.

SELECT 
    Sourcing_Channel,
    SUM(Recruitment_Cost) AS Total_Recruitment_Spend,
    SUM(CAST(p.Premium_Amount AS BIGINT)) AS Total_Premium,
    -- Prevent divide by zero errors
    CASE 
        WHEN SUM(Recruitment_Cost) = 0 THEN 0 
        ELSE SUM(CAST(p.Premium_Amount AS BIGINT)) / SUM(Recruitment_Cost) 
    END AS ROI_Multiplier
FROM dbo.agents a
JOIN dbo.policies p ON a.Agent_ID = p.Agent_ID
GROUP BY Sourcing_Channel
ORDER BY ROI_Multiplier DESC;

-- Agent 30-Day Activation Rate
-- The Business Question: In agency management, if an agent doesn't sell quickly, they usually quit.
-- What percentage of our agents sold their first policy within 30 days of onboarding?
-- What it proves: Advanced date manipulation (DATEDIFF), Common Table Expressions (CTEs), and complex logic.

WITH FirstSale AS (
    SELECT 
        Agent_ID, 
        MIN(Issue_Date) AS First_Policy_Date
    FROM dbo.policies
    GROUP BY Agent_ID
)
SELECT 
    a.Sourcing_Channel,
    COUNT(a.Agent_ID) AS Total_Agents,
    SUM(CASE WHEN DATEDIFF(day, a.Onboarding_Date, fs.First_Policy_Date) <= 30 THEN 1 ELSE 0 END) AS Activated_in_30_Days,
    CAST(SUM(CASE WHEN DATEDIFF(day, a.Onboarding_Date, fs.First_Policy_Date) <= 30 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(a.Agent_ID) * 100 AS Activation_Percentage
FROM dbo.agents a
LEFT JOIN FirstSale fs ON a.Agent_ID = fs.Agent_ID
GROUP BY a.Sourcing_Channel
ORDER BY Activation_Percentage DESC;

-- Policy Lapse Risk by Channel
-- certain channels bringing in agents who sell bad policies (policies that lapse or get surrendered)?

SELECT 
    a.Sourcing_Channel,
    COUNT(p.Policy_ID) AS Total_Policies,
    SUM(CASE WHEN p.Status IN ('Lapsed', 'Surrendered') THEN 1 ELSE 0 END) AS Bad_Policies,
    CAST(SUM(CASE WHEN p.Status IN ('Lapsed', 'Surrendered') THEN 1 ELSE 0 END) AS FLOAT) / COUNT(p.Policy_ID) * 100 AS Lapse_Rate_Percentage
FROM dbo.agents a
JOIN dbo.policies p ON a.Agent_ID = p.Agent_ID
GROUP BY a.Sourcing_Channel
ORDER BY Lapse_Rate_Percentage DESC;

