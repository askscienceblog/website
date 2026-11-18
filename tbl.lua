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

  if FORMAT == "context" then
    -- Code block as-is, caption paragraph after it.
    return {
      cb,
      pandoc.RawBlock('context', '\\start\n\\setupindenting[no]\\tfx\\setupinterlinespace'),
      pandoc.Para(caption_inlines),
      pandoc.RawBlock('context', '\\stop')
    }
  end

  -- Move any identifier onto the Figure so cross-references target the
  -- float rather than the bare code block.
  local id = cb.identifier
  cb.identifier = ""

  -- Wrap the inlines in a SINGLE Plain block: passing a bare inline list
  -- makes pandoc coerce each inline into its own Plain block, which the
  -- writer later rejoins with LineBreaks.
  return pandoc.Figure(
    { cb },
    pandoc.Caption({ pandoc.Plain(caption_inlines) }),
    { id = id }
  )
end

if FORMAT:match('context') then
  -- `page`/`pagewide` floats, moved to the end of the document (see Div and Pandoc below)
  local deferred = {}

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
    elseif el.classes:includes('pagewide') or el.classes:includes('page') then
      -- give the inner table/figure a page of its own: `page` upright, `pagewide` rotated 90°.
      -- A `page` float placed after \stopcolumnset is only saved, and is never output unless
      -- another float happens to be pending, so instead break the page and place it right there.
      local loc = el.classes:includes('pagewide') and '90,force,here,nonumber' or 'force,here,nonumber'
      local s = pandoc.write(pandoc.Pandoc(el.content), 'context')
      s = s:gsub('\\startplacetable%[', '\\startplacetable[location={' .. loc .. '},', 1)
      s = s:gsub('\\startplacefigure%[', '\\startplacefigure[location={' .. loc .. '},', 1)
      -- Breaking the columns here would leave the page before it part empty, so the float is set
      -- on its own page at the end of the document instead; only the page this point is shipped
      -- on is recorded, and the page is put back right after that page when the PDF is written.
      deferred[#deferred + 1] = s
      return pandoc.RawBlock('context', '\\latelua{userdata.pagewide.anchors[' .. #deferred .. ']=tex.getcount("realpageno")}')
    end
  end

  local function append_meta(meta, key, block)
    local value = meta[key]
    if value == nil then
      meta[key] = pandoc.MetaList { pandoc.MetaBlocks { block } }
    elseif pandoc.utils.type(value) == 'List' then
      value:insert(pandoc.MetaBlocks { block })
    else
      meta[key] = pandoc.MetaList { value, pandoc.MetaBlocks { block } }
    end
  end

  function Pandoc(doc)
    if #deferred == 0 then
      return nil
    end
    -- Before the first page: number each page by its place in the reordered PDF (body pages after
    -- a moved float shift up by one, a moved float takes the number after its anchor page), and
    -- put the licence on the page that ends up last.
    append_meta(doc.meta, 'header-includes', pandoc.RawBlock('context', [[
\startluacode
userdata.pagewide = { anchors = { }, starts = { }, current = false }
local pw = userdata.pagewide
function pw.number()
    local r = tex.getcount("realpageno")
    local n = r
    if pw.current then
        n = pw.anchors[pw.current] + pw.current
    else
        for _, a in pairs(pw.anchors) do
            if a < r then
                n = n + 1
            end
        end
    end
    context.setuppagenumber { number = n }
end
function pw.reorder()
    local floats = #pw.starts
    local pages = tex.getcount("realpageno") - 1
    local body = pages - floats
    local order = { }
    for r = 1, body do
        order[#order + 1] = r
        for i = 1, floats do
            if pw.anchors[i] == r then
                order[#order + 1] = pw.starts[i]
            end
        end
    end
    for i = 1, floats do
        if pw.starts[i] ~= body + i or not pw.anchors[i] or pw.anchors[i] > body then
            error("pagewide: float " .. i .. " has no page of its own or no anchor page")
        end
    end
    lpdf.setpageorder(order)
end
\stopluacode
\gdef\IfLastPageTF#1#2{\ifnum\pagenumber=\lastrealpage\relax#1\else#2\fi}
\appendtoks \ctxlua{userdata.pagewide.number()}\to\everybeforeshipout
]]))
    -- After the notes: each float on a page of its own, then the pages are put in order.
    local s = '\\stopcolumnset\n'
    for i, float in ipairs(deferred) do
      s = s .. '\\page\n\\ctxlua{userdata.pagewide.current=' .. i .. '}\\latelua{userdata.pagewide.starts[' .. i .. ']=tex.getcount("realpageno")}\n' .. float .. '\n'
    end
    s = s .. '\\page\n\\ctxlua{userdata.pagewide.reorder()}\n\\startcolumnset[main]'
    append_meta(doc.meta, 'include-after', pandoc.RawBlock('context', s))
    return doc
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
