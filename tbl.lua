function Table(tbl)
  tbl.colspecs = tbl.colspecs:map(function(colspec)
    local align = colspec[1]
    local width = nil
    return { align, width }
  end)

  local cap = tbl.caption
  -- Only transform tables that actually carry a caption.
  if not cap or not cap.long or #cap.long == 0 or not FORMAT:match("html") then
    return tbl
  end

  -- Grab the caption, then strip it from the table so the table itself
  -- renders with no <caption>.
  local long, short = cap.long, cap.short
  tbl.caption = { long = {}, short = nil }

  -- Wrap the now-captionless table in a Figure and hand the Figure the
  -- caption; the HTML writer turns that into the <figcaption>.
  return pandoc.Figure({ tbl }, { long = long, short = short })
end
