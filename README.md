%% Swimlane Diagram for Connecting Marketing Data to Google Sheets Dashboard

graph TB
  %% Define swimlanes
  subgraph Access_Platforms[Step 1: Gain Access to Platforms]
    A1[Accept Invitations to Klaviyo, Mailchimp, GA4, Facebook Ads]
    A2[Confirm Correct Access Levels (View or Analyst)]
    A3[Verify Ability to Export Reports]
  end

  subgraph Data_Imports[Step 2: Set Up Data Imports]
    B1[Automate Klaviyo Data (Zapier/Google Apps Script)]
    B2[Automate Mailchimp Data (Zapier/Google Apps Script)]
    B3[Set Up Google Analytics Add-on for Google Sheets]
    B4[Export Facebook Ads Performance Reports (Manual/Automated)]
  end

  subgraph Dashboard_Creation[Step 3: Create Google Sheets Dashboard]
    C1[Create Separate Sheets for Klaviyo, Mailchimp, GA4, Facebook Ads]
    C2[Structure Data with Formulas, Filters, Pivot Tables]
    C3[Create Summary Dashboard (Email, Web, Ads Performance)]
    C4[Format Dashboard (Conditional Formatting, Charts)]
  end

  subgraph Automation[Step 4: Automate Report Updates]
    D1[Schedule GA4 Data Refresh]
    D2[Set Up Automated Reports for Klaviyo & Mailchimp]
    D3[Establish Weekly Workflow for Facebook Ads Data]
  end

  subgraph Finalization[Step 5: Share Dashboard & Finalize]
    E1[Grant View-Only Access to Project Owner]
    E2[Review Dashboard Functionality]
    E3[Submit Final Report (Setup, Automation, Maintenance)]
  end

  %% Flow connections
  A1 --> A2 --> A3 --> B1
  A3 --> B2
  A3 --> B3
  A3 --> B4

  B1 --> C1
  B2 --> C1
  B3 --> C1
  B4 --> C1

  C1 --> C2 --> C3 --> C4 --> D1
  C4 --> D2
  C4 --> D3

  D1 --> E1
  D2 --> E1
  D3 --> E1

  E1 --> E2 --> E3
