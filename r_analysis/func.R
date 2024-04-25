
QueryRawDataTransportation <- function() {

  require(bigrquery)
  require(DBI)

  con <- dbConnect(
    bigrquery::bigquery(),
    project = "tiki-dwh",
    # dataset = "marketplace",
    billing = "369139100633"
  )

  sql <- function() {
    "
  with PBG as
    (
    select
          rl.request_id,
          created_at transferred,
          driver_name,
          datetime(expected_delivery_date,'+7')expected_delivery_date,
          count( distinct created_at) over (partition by request_id) count_pbg,
          ROW_NUMBER() OVER (PARTITION BY rl.ref_code ORDER BY rl.created_at DESC) AS max_rn
    from tnsl-dwh.tms.runsheet_lines rl
    where true
    and rl.created_at >= '2021-12-22'
    and rl.task_type IN ('direct_delivery', 'delivery')
        )
    , delivered_at  AS
    (
    select box_id,
        datetime_add(min(updated_time), interval 14 hour) order_delivered_at
     from tnsl-dwh.tms.request_box_history h
     where true
     and (h.status = 'successful_delivery' or h.sub_status = 'successful_delivery')
     and updated_time >= '2021-12-22'
     group by 1
    )
    select distinct tracking_id,
    client_order_id,
    o.order_created_at created_at,
    coalesce(t.status, sh.status) status,
    datetime(sh.created_at,'+14')  transferred,
    al.created_at allocated_at,
    coalesce(datetime(c.pickup_at,'+7'), h.created_at ) pickup_at,
    -- datetime(c.delivered_at,'+7') delivered_at_checkpoints,
    case when ser.code = 'p2p_direct' then coalesce(datetime(c.delivered_at,'+7'), datetime(d.order_delivered_at))
      else sd.created_at end
         delivered_at,
    trg.created_at triggered_at,
    '' reason_return,
    r.created_at returned_at,
    datetime_diff(al.created_at, datetime(sh.created_at,'+14'),minute)/60 leadtime_allocate,
    datetime_diff(coalesce(datetime(c.pickup_at,'+7'), h.created_at ),al.created_at,minute)/60 leadtime_pickup,
    case when ser.code = 'p2p_direct' then datetime_diff(coalesce(datetime(c.delivered_at,'+7'), datetime(d.order_delivered_at)),datetime(c.pickup_at,'+7'),minute)/60
      when ser.code <> 'p2p_direct' then datetime_diff(sd.created_at,h.created_at,minute)/60
        end  leadtime_delivery,
    datetime_diff(r.created_at,trg.created_at,minute)/60 leadtime_FD,
    case when ser.code = 'p2p_direct' then
          case when datetime_diff(coalesce(datetime(c.delivered_at,'+7'), datetime(d.order_delivered_at)),datetime(c.pickup_at,'+7'),minute) <60 then 1 else 0 end
         when ser.code <> 'p2p_direct' then
         case when datetime_diff(sd.created_at,h.created_at,minute)/60 <60 then 1 else 0 end end is_ontime,
    ser.partner_code partner,
    ser.code shipping_mode,
    case when ser.code = 'p2p_direct' then 'p2p_ted' else 'p2p_partner' end metric,
    sh.distance
    from tnsl-dwh.tiki_logiapi.shipments sh
    join tnsl-dwh.dwh_public.fact_order_process o on o.order_no = sh.client_order_id and date(order_created_at)>= '2022-01-01'
    left join tnsl-dwh.tiki_logiapi.services ser on sh.service_id = ser.id
    left join tnsl-dwh.tms.request_box_tracking t on sh.tracking_id = t.client_ref_Code
    left join tnsl-dwh.tms.request_box_checkpoints c on c.box_id = t.request_box_id
    left join PBG a on t.request_id = a.request_id --and a.max_rn =1
    left join delivered_at d on d.box_id = t.request_box_id
    left join (select shipment_id,
                      datetime(max(created_at),'+14')created_at,
                      from  tnsl-dwh.tiki_logiapi.shipment_histories
                       where true
                       and status = 'picking'
                       group by 1
                       order by created_at
     ) al on al.shipment_id = sh.id
    left join (select shipment_id,
                      datetime(min(created_at),'+14')created_at,
                      from  tnsl-dwh.tiki_logiapi.shipment_histories
                       where true
                       and status = 'delivering'
                       group by 1
                       order by created_at
     ) h on h.shipment_id = sh.id
     left join (select shipment_id,
                      datetime(min(created_at),'+14')created_at,
                      from  tnsl-dwh.tiki_logiapi.shipment_histories
                       where true
                       and status = 'successful_delivery'
                       group by 1
                       order by created_at
     ) sd on sd.shipment_id = sh.id
      left join (select shipment_id,
                      datetime(min(created_at),'+14')created_at,
                      from  tnsl-dwh.tiki_logiapi.shipment_histories
                       where true
                       and status = 'returning'
                       group by 1
                       order by created_at
     ) trg on trg.shipment_id = sh.id
     left join (select shipment_id,
                      datetime(min(created_at),'+14')created_at,
                      from  tnsl-dwh.tiki_logiapi.shipment_histories
                       where true
                       and status = 'returned'
                       group by 1
                       order by created_at
     ) r on r.shipment_id = sh.id
    where true
    and date(o.order_created_at) >= date_sub(current_date, interval 150 day)
    and ser.code not in ('hns_standard','hns')
    order by created_at desc
    "
  }

  RawDataTransportation <- dbGetQuery(con, sql())

  save(RawDataTransportation, file = "DATA/RawDataTransportation.Rdata")


}



QuerySalesOrderData <- function() {

  require(bigrquery)
  require(DBI)

  con <- dbConnect(
    bigrquery::bigquery(),
    project = "tiki-dwh",
    # dataset = "marketplace",
    billing = "369139100633"
  )

  sql <- function() {

    "WITH raw_order AS (select
        DISTINCT
        sales.order_id,
        sales.order_created_at,
        sales.order_confirmed_at,
        sales.order_code,
        sales.order_model,
        sales.order_general_status,
        sales.seller_id,
        sales.seller_name,
        sales.warehouse_name,
        sales.sku_business_type,
        dp.inventory_type_name,
        sales.sku,
        sales.product_name,
        sales.cate_report,
        sales.sub_cate_report,
        sales.product_qty,
        sales.customer_id,
        sales.customer_region,
        sales.customer_province,
        sales.customer_district,
        sales.customer_ward,
        sales.cate1,
        sales.cate2,
        case  when dp.cate2_id in (54276, 54290, 54302, 44824, 54316, 44832, 54344, 54430) then 'FRESH'
            when dp.cate2_id in (54330, 54362, 54412, 54452, 54398, 54384, 54438, 54466) then 'FMCG'
            when dp.cate2_id in (54474, 54500, 54514) then 'NON-FOOD'
      end as tikingon_cate_report,
        sales.order_created_at as order_date,
        date(sfs.date) as first_salable_date,
        sales.is_fresh_p2p,
        sales.shipping_type,
        sales.returned_to_seller_at
        from tiki-dwh.marketplace.fact_order_master_data sales
        left join tiki-dwh.dwh.dim_product_full dp on dp.sku = sales.sku
        left join tiki-dwh.marketplace.metric_selection_first_salable sfs on sfs.product_id = dp.product_key
        where 1=1
        --AND sales.seller_id = 243693
        --AND sku_business_type = '1P'
        --AND sku_inventory_type = 'instock'
        --AND date(sales.order_created_at) >= '2021-12-01'
        AND dp.is_free_gift = FALSE
        AND date(sales.order_created_at) >=  DATE_SUB(CURRENT_DATE('+7'), INTERVAL 120 day)
        --AND sales.order_general_status in ('complete', 'canceled')
        AND sales.sub_cate_report = 'TIKI-Ngon'
        )
        , nmv as (
            select order_code,
            sku,
            sum(nmv) as nmv
            from `tiki-dwh.nmv.nmv`
            group by 1,2
        )
        SELECT DISTINCT
        *
        from raw_order sales
        left join nmv USING(order_code, sku)
    "

  }


  RawSalesOrder <- dbGetQuery(con, sql())
  save(RawSalesOrder, file = "DATA/RawSalesOrder.Rdata")

}

QuerySalesOrderData()









