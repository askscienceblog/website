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

local function flank(blocks, before, after)
  local out = pandoc.List{ pandoc.RawBlock('context', before) }
  out:extend(blocks)
  out:insert(pandoc.RawBlock('context', after))
  return out
end

function Div(el)
  if el.classes:includes('wide') then
    return flank(el.content, '\\startcolumnsetspan[wide]', '\\stopcolumnsetspan')

  elseif el.classes:includes('page') then
    -- render the inner table, then turn its float into a rotated page float
    local s = pandoc.write(pandoc.Pandoc(el.content), 'context')
    s = s:gsub('\\startplacetable%[', '\\startplacetable[location={90,page},', 1)
    return pandoc.RawBlock('context', s)
  end
end

if FORMAT:match('context') then
  function Figure(fig)
    return fig:walk{
      Image = function(img)
        img.attributes.width = '95%'
        return img
      end
    }
  end
end
