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

function CodeBlock(cb)
  local caption = cb.attributes.caption
  if not caption then
    return nil
  end
  cb.attributes.caption = nil

  -- Parse the caption as Markdown so inline formatting / math survive.
  local caption_inlines = pandoc.utils.blocks_to_inlines(
    pandoc.read(caption, "markdown").blocks
  )

  -- Move any identifier onto the Figure so cross-references target the
  -- float rather than the bare code block.
  local id = cb.identifier
  cb.identifier = ""

  return pandoc.Figure(
    { cb },
    pandoc.Caption(caption_inlines),
    { id = id }
  )
end

if FORMAT:match('context') then
  function Div(el)
    if el.classes:includes('wide') then
      local s = pandoc.write(pandoc.Pandoc(el.content), 'context')
      local num_cols
      for _, block in ipairs(el.content) do
        if block.t == 'Table' then
          num_cols = #block.colspecs
          break
        end
      end
      return pandoc.RawBlock('context', s:gsub('\\startxtable', '\\startxtable[width=' .. 150 / num_cols .. 'mm]', 1))
    elseif el.classes:includes('pagewide') then
      -- render the inner table, then turn its float into a rotated page float
      local s = pandoc.write(pandoc.Pandoc(el.content), 'context')
      s = s:gsub('\\startplacetable%[', '\\startplacetable[location={90,page,nonumber},', 1)
      return pandoc.RawBlock('context', '\\stopcolumnset\n' .. s .. '\n\\page\\startcolumnset[main]')
    elseif el.classes:includes('page') then
      -- render the inner table, then turn its float into a rotated page float
      local s = pandoc.write(pandoc.Pandoc(el.content), 'context')
      s = s:gsub('\\startplacetable%[', '\\startplacetable[location={page,nonumber},', 1)
      return pandoc.RawBlock('context', '\\stopcolumnset\n' .. s .. '\n\\page\\startcolumnset[main]')
    end
  end

  function Figure(fig)
    return fig:walk {
      Image = function(img)
        img.attributes.width = '95%'
        return img
      end
    }
  end
end
