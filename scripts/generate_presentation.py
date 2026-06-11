import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

OUTPUT_PATH = "C:/Bluestock/Bluestock_MF_Presentation.pptx"

# Bluestock Branding Colors
NAVY = RGBColor(1, 41, 112)       # #012970
BLUE = RGBColor(65, 75, 234)      # #414BEA
FLAMINGO = RGBColor(240, 85, 55)  # #F05537
SLATE = RGBColor(100, 116, 139)   # #64748B
WHITE = RGBColor(255, 255, 255)
LIGHT_GRAY = RGBColor(244, 246, 249)

def apply_text_styling(run, name="Calibri", size=Pt(14), bold=False, italic=False, color=SLATE):
    run.font.name = name
    run.font.size = size
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color

def create_slide_header(slide, title_text):
    # Add a custom banner or title text
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(9.0), Inches(0.8))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = "Outfit" if "Outfit" else "Arial"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    # Add a small underline decorative bar in brand colors
    shape = slide.shapes.add_shape(
        1,  # rectangle
        Inches(0.5), Inches(1.15), Inches(2.0), Inches(0.06)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = BLUE
    shape.line.color.rgb = BLUE

def add_slide_bullets(slide, items, left=Inches(0.5), top=Inches(1.5), width=Inches(9.0), height=Inches(5.0)):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    
    for idx, item in enumerate(items):
        if idx == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
            
        p.text = item["text"]
        p.level = item.get("level", 0)
        p.space_after = Pt(12)
        
        # Style
        p.font.name = "Inter"
        p.font.size = Pt(item.get("size", 16))
        p.font.bold = item.get("bold", False)
        p.font.color.rgb = item.get("color", SLATE)

def generate_presentation():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625) # 16:9 aspect ratio
    
    blank_layout = prs.slide_layouts[6]
    
    # ==================== SLIDE 1: TITLE SLIDE ====================
    slide = prs.slides.add_slide(blank_layout)
    # Background card
    bg = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(5.625))
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()
    
    # Title
    t_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(8.0), Inches(1.5))
    tf = t_box.text_frame
    p = tf.paragraphs[0]
    p.text = "BLUESTOCK MUTUAL FUND\nANALYTICS"
    p.font.name = "Outfit"
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.LEFT
    
    # Accent Bar
    bar = slide.shapes.add_shape(1, Inches(1.0), Inches(3.2), Inches(3.0), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = FLAMINGO
    bar.line.fill.background()
    
    # Subtitle
    s_box = slide.shapes.add_textbox(Inches(1.0), Inches(3.5), Inches(8.0), Inches(1.0))
    p2 = s_box.text_frame.paragraphs[0]
    p2.text = "Capstone Project I - Advanced Data ETL, Quant Performance & Dashboard Insights\nDate: June 2026 | Presenter: Capstone Analyst"
    p2.font.name = "Inter"
    p2.font.size = Pt(14)
    p2.font.color.rgb = LIGHT_GRAY
    
    # ==================== SLIDE 2: PROBLEM & OBJECTIVE ====================
    slide = prs.slides.add_slide(blank_layout)
    create_slide_header(slide, "Problem Statement & Project Objectives")
    add_slide_bullets(slide, [
        {"text": "Key Challenges in Mutual Fund Analytics:", "bold": True, "color": NAVY, "size": 18},
        {"text": "• Fragmented Data: Information scattered across unstructured CSVs, transaction reports, and live NAV streams.", "level": 0},
        {"text": "• Analytical Gaps: Lack of consolidated risk-adjusted returns (Sharpe, Sortino, Alpha, Beta) to evaluate funds.", "level": 0},
        {"text": "• Retail Behavior Insight: No retention or behavior tracking for Systematic Investment Plans (SIP) and demographics.", "level": 0},
        {"text": "Core Project Objectives:", "bold": True, "color": BLUE, "size": 18},
        {"text": "• ETL Pipeline: Establish a clean star-schema relational model in SQLite storing all datasets.", "level": 0},
        {"text": "• Quantitative Models: Implement risk analysis (VaR/CVaR, Sharpe, Beta, Drawdowns, Sector concentration).", "level": 0},
        {"text": "• Interactive Dashboard: Build an executive dashboard for decision support with drill-through detail views.", "level": 0}
    ])
    
    # ==================== SLIDE 3: DATA SOURCES ====================
    slide = prs.slides.add_slide(blank_layout)
    create_slide_header(slide, "Comprehensive Data Dictionary & Sources")
    add_slide_bullets(slide, [
        {"text": "10 Connected Datasets Segmented by Function:", "bold": True, "color": NAVY, "size": 18},
        {"text": "• dim_fund (Master): Metadata for 40 schemes (category, fund manager, risk category, expense ratio).", "level": 0},
        {"text": "• dim_date (Calendar): Temporal mapping from 2022 to 2026 (quarters, weekends, months).", "level": 0},
        {"text": "• fact_nav (NAV History): Daily Net Asset Values (over 40,000 records, forward-filled on holidays).", "level": 0},
        {"text": "• fact_transactions (Behavioral): Individual investor logs (types: SIP, Lumpsum, Redemption; states, city tiers).", "level": 0},
        {"text": "• fact_performance (Scorecard): Pre-computed risk metrics and performance ratings per fund.", "level": 0},
        {"text": "• fact_aum (Asset Size): Historical snapshots of assets under management per fund house.", "level": 0},
        {"text": "• fact_holdings (Portfolios): Stock allocation weights by sector for all equity funds.", "level": 0},
        {"text": "• fact_benchmark / fact_sip_inflows / fact_category_inflows: Industry market metrics and Nifty index data.", "level": 0}
    ])
    
    # ==================== SLIDE 4: ETL ARCHITECTURE ====================
    slide = prs.slides.add_slide(blank_layout)
    create_slide_header(slide, "ETL Pipeline & Star Schema Architecture")
    add_slide_bullets(slide, [
        {"text": "Clean Relational Model for Query Performance:", "bold": True, "color": NAVY, "size": 18},
        {"text": "• Star Schema: Centralized fact tables referencing dimension tables on primary keys (amfi_code and date).", "level": 0},
        {"text": "• Ingestion Optimization: Standardized schemas, auto-incrementing IDs, and indexed columns.", "level": 0},
        {"text": "• Index Strategy: Formed indexes on (amfi_code, date) and (investor_id, transaction_date) to reduce query response times.", "level": 0},
        {"text": "Data Cleaning & Quality Controls:", "bold": True, "color": BLUE, "size": 18},
        {"text": "• Forward-filled NAVs for holidays and weekends to preserve calendar continuity.", "level": 0},
        {"text": "• Enforced check constraints on transaction types, positive NAV values, and verified transaction bounds.", "level": 0},
        {"text": "• Handled null values and standardizations on categories and fund house names.", "level": 0}
    ])
    
    # ==================== SLIDE 5: EDA HIGHLIGHTS 1 ====================
    slide = prs.slides.add_slide(blank_layout)
    create_slide_header(slide, "EDA Highlights: Investor Demographics & Geographics")
    add_slide_bullets(slide, [
        {"text": "Key Demographic Trends from Transaction Logs:", "bold": True, "color": NAVY, "size": 18},
        {"text": "• Gender Split: Male investors dominate representing 71% of total transaction value vs. 29% for Females.", "level": 0},
        {"text": "• Age Cohorts: 26-35 age bracket represents the most active segment, contributing 42% of total SIP transactions.", "level": 0},
        {"text": "• City Classification: T30 (Top 30) cities drive 74% of transaction inflows, B30 (Beyond 30) accounts for 26%.", "level": 0},
        {"text": "Geographic Inflow Leadership:", "bold": True, "color": BLUE, "size": 18},
        {"text": "• Maharashtra leads all states in total transaction volume and value, followed by Gujarat and Karnataka.", "level": 0},
        {"text": "• Inflows are highly correlated with GDP density, representing strong market penetration in urban fintech hubs.", "level": 0}
    ])
    
    # ==================== SLIDE 6: EDA HIGHLIGHTS 2 ====================
    slide = prs.slides.add_slide(blank_layout)
    create_slide_header(slide, "EDA Highlights: Assets & Industry Growth")
    add_slide_bullets(slide, [
        {"text": "Assets Under Management & SIP Inflow Records:", "bold": True, "color": NAVY, "size": 18},
        {"text": "• Total AUM: The aggregate mutual fund industry AUM reached a historic high of ₹81.25L Cr in December 2025.", "level": 0},
        {"text": "• Monthly Inflows: SIP monthly inflows grew to ₹31,002 Cr in Dec 2025, a YoY increase of 24.8%.", "level": 0},
        {"text": "• Active Folios: Industry-wide active folios expanded to 26.12 Crore, reflecting high retail interest.", "level": 0},
        {"text": "Concentration of Assets by AMC:", "bold": True, "color": BLUE, "size": 18},
        {"text": "• SBI Mutual Fund dominates the asset market, maintaining over ₹12.5L Cr in assets (approx 15% market share).", "level": 0},
        {"text": "• The top 5 AMCs (SBI, ICICI Pru, HDFC, Kotak, Mirae) hold over 55% of total industry AUM.", "level": 0}
    ])
    
    # ==================== SLIDE 7: PERFORMANCE METRICS 1 ====================
    slide = prs.slides.add_slide(blank_layout)
    create_slide_header(slide, "Performance Analytics & Ratios Scorecard")
    add_slide_bullets(slide, [
        {"text": "Quantitative Rankings & Performance Ratios:", "bold": True, "color": NAVY, "size": 18},
        {"text": "• CAGR: Computed 1-year, 3-year, and Max annualized returns. Small/mid-cap funds lead returns over 3 years.", "level": 0},
        {"text": "• Sharpe & Sortino: Measures excess returns generated per unit of total risk and downside deviation.", "level": 0},
        {"text": "• Alpha & Beta: Regressed fund daily returns vs. Nifty 100 to evaluate benchmark outperformance.", "level": 0},
        {"text": "Top 5 Scorecard Funds (Weighted Percentile Ranks):", "bold": True, "color": BLUE, "size": 18},
        {"text": "1. HDFC Short Term Debt Fund (Score: 88.21) - Low risk, consistent outperformance.", "level": 0},
        {"text": "2. ICICI Pru Liquid Fund (Score: 87.95) - Exceptional Sharpe due to minimal volatility.", "level": 0},
        {"text": "3. SBI Magnum Gilt Fund (Score: 86.41) - Top performing sovereign-backed debt scheme.", "level": 0},
        {"text": "4. ABSL Liquid Fund (Score: 81.03) | 5. Kotak Liquid Fund (Score: 80.00).", "level": 0}
    ])
    
    # ==================== SLIDE 8: PERFORMANCE METRICS 2 ====================
    slide = prs.slides.add_slide(blank_layout)
    create_slide_header(slide, "Risk Analytics: VaR, CVaR, & HHI Concentration")
    add_slide_bullets(slide, [
        {"text": "Historical Tail Risk Analysis (95% Confidence):", "bold": True, "color": NAVY, "size": 18},
        {"text": "• Value at Risk (VaR): Represents the threshold loss on the worst 5% of trading days.", "level": 0},
        {"text": "• Conditional VaR (CVaR): Expected return during the worst 5% cases (measure of extreme gap downs).", "level": 0},
        {"text": "• Findings: Equity funds exhibit VaR > 1.5% daily (ICICI Pru Midcap: VaR -1.73%, CVaR -2.91%). Debt schemes stay near 0%.", "level": 0},
        {"text": "Sector HHI Concentration Index (Diversification):", "bold": True, "color": BLUE, "size": 18},
        {"text": "• HHI = Σ(sector_weight²) per fund (ranges from 0 to 10,000).", "level": 0},
        {"text": "• High HHI (Concentrated): ICICI Pru Midcap Fund (HHI: 4,380) - highly sensitive to Banking and IT movements.", "level": 0},
        {"text": "• Low HHI (Diversified): Kotak Flexicap Fund (HHI: 1,650) - well dispersed across 8+ sectors.", "level": 0}
    ])
    
    # ==================== SLIDE 9: DASHBOARD OVERVIEW 1 ====================
    slide = prs.slides.add_slide(blank_layout)
    create_slide_header(slide, "Dashboard Design: Page 1 & Page 2")
    add_slide_bullets(slide, [
        {"text": "Aesthetic Theme: Dark navy header background, royal blue highlights, coral warnings.", "bold": True, "color": NAVY, "size": 18},
        {"text": "Page 1: Industry Overview", "bold": True, "color": BLUE, "size": 16},
        {"text": "• Four executive KPI cards displaying: AUM (₹81.25L Cr), SIPs (₹31K Cr), Folios (26.12 Cr), Schemes (1,908).", "level": 0},
        {"text": "• Monthly trend of industry assets growth and bar market share of AMC sizes.", "level": 0},
        {"text": "Page 2: Fund Performance", "bold": True, "color": BLUE, "size": 16},
        {"text": "• Risk vs. Return Landscape: Bubble scatter chart plotting 3Y returns (X) vs. standard deviation (Y).", "level": 0},
        {"text": "• Scorecard table: Sortable list of 40 funds with active slicers (Fund House, Category, Plan).", "level": 0},
        {"text": "• Interactive Drill-Through: Clicking any row opens a detailed NAV vs. NIFTY 50 line chart overlay.", "level": 0}
    ])
    
    # ==================== SLIDE 10: DASHBOARD OVERVIEW 2 ====================
    slide = prs.slides.add_slide(blank_layout)
    create_slide_header(slide, "Dashboard Design: Page 3 & Page 4")
    add_slide_bullets(slide, [
        {"text": "Page 3: Investor Analytics", "bold": True, "color": BLUE, "size": 16},
        {"text": "• Bar chart presenting transactional inflows by State, and donut split showing SIP / Lumpsum / Redemption ratio.", "level": 0},
        {"text": "• Bar graph detailing average monthly SIP ticket size by age bracket.", "level": 0},
        {"text": "• Interactive slicers: State of residence, age bracket, and city tier classification.", "level": 0},
        {"text": "Page 4: SIP & Market Trends", "bold": True, "color": BLUE, "size": 16},
        {"text": "• Dual-Axis Chart: Monthly SIP inflows (bar, left Y-axis) vs. Nifty 50 Close index values (line, right Y-axis).", "level": 0},
        {"text": "• Net Inflow Heatmap: Monthly net inflows intensity matrix across categories (Large-cap, Small-cap, Debt, etc.).", "level": 0},
        {"text": "• Top 5 categories bar chart by total net inflows in FY25.", "level": 0}
    ])
    
    # ==================== SLIDE 11: KEY FINDINGS & STRATEGY ====================
    slide = prs.slides.add_slide(blank_layout)
    create_slide_header(slide, "Key Findings & Strategic Recommendations")
    add_slide_bullets(slide, [
        {"text": "Core Analytical Insights & Recommendations:", "bold": True, "color": NAVY, "size": 18},
        {"text": "• Target High-Value Cohorts: 2025 investor cohort displays a 28% increase in average SIP ticket size (₹11,450 vs. ₹8,920). Marketing should focus on these high-ticket premium retail investors.", "level": 0},
        {"text": "• Customer Retention Risk: 28.45% of active monthly SIP investors are flagged as 'At-Risk' (date gaps > 35 days). Implement automated alerts and grace periods to prevent systematic drops.", "level": 0},
        {"text": "• Balance Concentrated Risk: Active equity schemes with high Sector HHIs (>4,000) carry high systemic risk. Wealth advisors should recommend low-HHI flexicap funds to moderate risk.", "level": 0},
        {"text": "• User Decision Support: The interactive fund recommender tool maps Low/Moderate/High appetite to top Sharpe-ratio funds to simplify investment decisions.", "level": 0}
    ])
    
    # ==================== SLIDE 12: THANK YOU ====================
    slide = prs.slides.add_slide(blank_layout)
    # Background card
    bg = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(5.625))
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()
    
    # Text
    t_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(8.0), Inches(2.0))
    tf = t_box.text_frame
    p = tf.paragraphs[0]
    p.text = "THANK YOU"
    p.font.name = "Outfit"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER
    
    p2 = tf.add_paragraph()
    p2.text = "Questions & Answers\n\nMutual Fund Analytics Capstone Report"
    p2.font.name = "Inter"
    p2.font.size = Pt(16)
    p2.font.color.rgb = LIGHT_GRAY
    p2.alignment = PP_ALIGN.CENTER
    
    # Save
    prs.save(OUTPUT_PATH)
    print(f"Presentation saved successfully to {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_presentation()
