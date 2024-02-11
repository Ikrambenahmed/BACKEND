from app.models.TRXCUR import TRXCUR
from app.infrastructure.ConnectDB import db, get_shared_connection
from flask import Blueprint
from flask import jsonify, request
from sqlalchemy import func
from sqlalchemy import text

api_getworkflow_blueprint = Blueprint('api_getTRXCURFUND', __name__)

@api_getworkflow_blueprint.route('/workflow/<string:fund>', methods=['GET'])
def filter_data_for_fund_and_date_range(fund):
    try:
        connection = get_shared_connection()

        query = """
        WITH DateSeries (process_date) AS (
    SELECT TO_DATE('10/01/2022', 'MM/DD/YYYY') -- Specify the start date
    FROM dual
    UNION ALL
    SELECT process_date + 1
    FROM DateSeries
    WHERE 
      process_date + 1 <= TO_DATE('10/30/2022', 'MM/DD/YYYY') -- Specify the end date
),
 ProcessRuns AS (
    SELECT
      ds.process_date,
      tr.fund,
      CASE
        WHEN tr.auttrx_no IS NOT NULL THEN 'Expense Accruals'
        WHEN tr.check_num = 'YROLL' THEN 'YROLL'
        WHEN tr.check_num LIKE 'M2M%' THEN 'M2MJE'
        WHEN tr.check_num = 'INTRF' THEN 'INTRF'
        WHEN tr.check_num IN ('CID', 'DID') THEN 'CASH DIST / RECIPT'
        WHEN tr.check_num IS NOT NULL THEN 'CASH DIST / RECIPT'
        WHEN tr.check_num IS NULL THEN 'JOURNAL ENTRY'
        ELSE 'Not Defined'
      END AS process_name,
      TO_NUMBER(SUBSTR(tr.enttime, 0, 2)) AS start_time,
      TO_NUMBER(SUBSTR(tr.enttime, 0, 2)) + 1 AS end_time
    FROM DateSeries ds
    LEFT JOIN trx tr ON TRUNC(tr.datent) = ds.process_date AND tr.trxcur_no IS NULL and tr.fund=:fund
    
    UNION ALL
    -- Logic for trxcur table
    SELECT
      ds.process_date,
      tr.fund,
      CASE
                 when tr.trxtyp in ('1110', '1113', '1114', '1115', '1117', '1118', '1119', '1120', '1121', '1125', '1127', '1130', '1135', '1137', '1140', '1145', '1147', '1180', '1190', '1192', '1193', '1350', '1370', '1380', '1390', '1440', '1445', '3125', '3135', '3136', '3137') then
                  'TRADE'
                 when tr.trxtyp in ('3110','1128') then
                  'DIVIDEND ACCRUAL'
                  when tr.trxtyp in ('1124','3120','3130','3132','3133') then
                  'AMORTIZATION/ACCRETION'
                   when tr.trxtyp in ('4161','1122','1123','1126','1129','1170','1175','1185','1480','1485') then
                  'CAPITAL EVENT'
                    when tr.trxtyp in ('4111') then
                  'DIVIDEND RECEIPT'
                    when tr.trxtyp in ('1240', '1245', '1250', '1255', '1260', '1330', '1340', '1360') then
                  'Int Rec, Cpns, Mat, Exp & Del'
                  when tr.trxtyp in ('4810', '4820', '4830', '4840', '4850', '4860', '4870', '4880', '4910', '4920', '4930', '4940') then
                  'SHAREHOLDER ACTIVITY'
                  when tr.trxtyp in ('5170','5175','5112', '5128', '5129', '5193', '5430', '5485', '6171', '6200', '8110', '8121', '8161', '8810', '8820', '8830', '8840', '8910', '8920') then
                  'SETTLE CAPITAL'
                   when tr.trxtyp in ('5192', '8111', '8131', '8171') then
                  'SETTLE INCOME'
                   when tr.trxtyp in ('5240','5245','5250','5255','5330') then
                  'SETTLE Maturity'
                  when tr.trxtyp in ('5110', '5115', '5120', '5121', '5125', '5130', '5135', '5140', '5145', '5480', '8132') then
                  'SETTLE Trade'
                     ELSE tp.lgdesc
      END AS process_name,
      TO_NUMBER(SUBSTR(tr.enttime, 0, 2)) AS start_time,
      TO_NUMBER(SUBSTR(tr.enttime, 0, 2)) + 1 AS end_time
    FROM DateSeries ds
    LEFT JOIN trxcur tr ON TRUNC(tr.entdat) = ds.process_date
    LEFT JOIN trxtyp tp ON tr.trxtyp = tp.trxtyp
    WHERE tr.fund=:fund
    
    UNION ALL
    --PRICE LOGIC
    
    SELECT
      ds.process_date,
      ph.fund,
      'Load Price' AS process_name,
      TO_NUMBER(SUBSTR(ph.pricetime, 0, 2)) AS start_time,
      TO_NUMBER(SUBSTR(ph.pricetime, 0, 2)) + 1 AS end_time
    FROM DateSeries ds
    LEFT JOIN prihst ph ON TRUNC(ph.prcdate) = ds.process_date AND ph.fund = :fund
    WHERE ph.prcdate = ds.process_date -- Adjust the date as needed

    UNION ALL
    -- Logic for NAVHST table
    SELECT
      ds.process_date,
      tr.fund,
      'NAV STRIKE' AS process_name,
      TO_NUMBER(SUBSTR(tr.ENTRY_TIME, 0, 2)) AS start_time,
      TO_NUMBER(SUBSTR(tr.ENTRY_TIME, 0, 2)) + 1 AS end_time
    FROM DateSeries ds
    LEFT JOIN NAVHST tr ON TRUNC(tr.ENTRY_DATE) = ds.process_date
    WHERE tr.ENTRY_DATE = ds.process_date and tr.fund=:fund

  ),
  DayOfWeekCounts AS (
    SELECT
      pr.fund,
      pr.process_name,
      TO_CHAR(ds.process_date, 'D') AS day_of_week,
      COUNT(DISTINCT ds.process_date) AS occurrences
    FROM ProcessRuns pr
    RIGHT JOIN DateSeries ds ON pr.process_date = ds.process_date
    GROUP BY pr.fund, pr.process_name, TO_CHAR(ds.process_date, 'D')
  ),
  TotalDaysOfWeek AS (
    SELECT
      TO_CHAR(ds.process_date, 'D') AS day_of_week,
      COUNT(DISTINCT ds.process_date) AS total_days_of_week
    FROM DateSeries ds
    GROUP BY TO_CHAR(ds.process_date, 'D')
  ),
  ProcessProbability AS (
    SELECT
      d.day_of_week,
      pr.fund,
      pr.process_name,
      NVL(dc.occurrences, 0) / td.total_days_of_week * 100 AS probability
    FROM (SELECT DISTINCT TO_CHAR(process_date, 'D') AS day_of_week FROM DateSeries) d
    CROSS JOIN (SELECT DISTINCT fund, process_name FROM ProcessRuns) pr
    LEFT JOIN DayOfWeekCounts dc ON d.day_of_week = dc.day_of_week AND pr.process_name = dc.process_name
    LEFT JOIN TotalDaysOfWeek td ON d.day_of_week = td.day_of_week
  )
SELECT
  pp.fund,
  pp.process_name,
  pp.day_of_week,
  NVL(pp.probability, 0) AS probability,
  ROUND(AVG(pr.start_time), 0) AS avg_start_time,
  ROUND(AVG(pr.end_time), 0) AS avg_end_time
FROM ProcessProbability pp
JOIN ProcessRuns pr ON pp.fund = pr.fund AND pp.process_name = pr.process_name
GROUP BY pp.fund, pp.process_name, pp.day_of_week, pp.probability
ORDER BY pp.fund, pp.process_name, pp.day_of_week
        """

        # Use SQLAlchemy's text method to bind parameters
        sql_query = text(query)

        # Bind parameters to the query using params method
        result = connection.execute(sql_query.params(fund=fund))

        fund_data = result.fetchall()

        # Get the column names from the result set
        columns = result.keys()

        # Convert the result into a list of dictionaries
        fund_data_list = [dict(zip(columns, row)) for row in fund_data]

        # Close the connection
        connection.close()

        return jsonify({'fund_data': fund_data_list})
    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in filter_data_for_fund_and_date_range: {str(e)}")
        return jsonify({'error': str(e)}), 500
