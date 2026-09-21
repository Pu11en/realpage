// Client-side Lead Pack PDF builder. The page supplies the leads already loaded
// for the chosen state/region; no server or paid AI call is involved.
(function (root, factory) {
  const api = factory(root);
  root.CraneSignalLeadPack = api;
  if (typeof module === "object" && module.exports) module.exports = api;
})(typeof globalThis !== "undefined" ? globalThis : window, function (root) {
  "use strict";

  const HOT_SCORE = 70;
  const WARM_SCORE = 40;
  const FOOTER = "Find who to call for any building at app.cranesignal.com";
  const APP_URL = "https://app.cranesignal.com";
  const CONTACT_CTA = "Get who to call >";
  const DOWNLOAD_DATE_KEY_PREFIX = "cranesignal.leadPack.lastDownloaded";

  function priorityForLead(lead) {
    const score = Number(lead.score) || 0;
    const signal = String(lead.signalType || lead.stage || "lead").toLowerCase();
    if (score >= HOT_SCORE) {
      return { label: "Hot", reason: `Strong ${signal} timing signal with a lead score of ${score}.` };
    }
    if (score >= WARM_SCORE) {
      return { label: "Warm", reason: `Solid ${signal} signal worth contacting soon, with a lead score of ${score}.` };
    }
    return { label: "Early", reason: `Early ${signal} signal to watch as more details appear, with a lead score of ${score}.` };
  }

  function whyNowSentence(lead) {
    const why = String(lead.why || lead.signal || "This building has a current lead signal")
      .replace(/\s*·\s*/g, ", ")
      .trim();
    return /[.!?]$/.test(why) ? why : `${why}.`;
  }

  function sourceForLead(lead) {
    const sources = Array.isArray(lead.sources) ? lead.sources : [];
    for (const source of sources) {
      if (typeof source === "string" && /^https?:\/\//i.test(source)) {
        return { label: "Open source", url: source };
      }
      if (source && /^https?:\/\//i.test(source.url || "")) {
        return { label: source.label || "Open source", url: source.url };
      }
    }
    for (const [label, url] of Object.entries(lead.links || {})) {
      if (/^https?:\/\//i.test(url || "")) return { label: label || "Open source", url };
    }
    if (/^https?:\/\//i.test(lead.website || "")) return { label: "Building website", url: lead.website };
    return { label: "Source not listed", url: "" };
  }

  function shortDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) return value;
    const [year, month, day] = value.split("-").map(Number);
    return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" })
      .format(new Date(Date.UTC(year, month - 1, day, 12)));
  }

  function timingForLead(lead) {
    if (lead.saleDate) return `Sold ${shortDate(lead.saleDate)}`;
    if (lead.openingDate) return `Opens ${shortDate(lead.openingDate)}`;
    if (lead.permitDate) return `Permit ${shortDate(lead.permitDate)}`;
    return "";
  }

  const STAGE_LABELS = {
    planned: "Planned", permitted: "Permit filed", permit: "Permit filed",
    "under construction": "Under construction", leasing: "Leasing now", sold: "Sold",
  };

  function stageForLead(lead) {
    const stage = STAGE_LABELS[lead.stage] || lead.stage || lead.signalType || "Stage not listed";
    const leasing = lead.signalType === "Leasing" && stage !== "Leasing now" ? " · leasing now" : "";
    const timing = timingForLead(lead);
    if (stage === "Sold" && timing.startsWith("Sold")) return timing;
    return [stage + leasing, timing].filter(Boolean).join("\n");
  }

  // Say whose number it is: the leasing office (from the building's website)
  // or the owner/developer office listed on the state building filing.
  function phoneForLead(lead) {
    if (lead.contact && lead.contact.phone) return { number: lead.contact.phone, label: "Leasing office" };
    if (lead.officePhone) return { number: lead.officePhone, label: lead.developer ? "Developer office" : "Project office" };
    return null;
  }

  function contactForLead(lead) {
    const lines = [];
    if (lead.owner) lines.push(`Owner: ${lead.owner}`);
    if (lead.developer) lines.push(`Developer: ${lead.developer}`);
    if (lead.buyer) lines.push(`Buyer: ${lead.buyer}`);
    const phone = phoneForLead(lead);
    if (phone) lines.push(`${phone.label}: ${phone.number}`);
    lines.push(CONTACT_CTA);
    return lines.join("\n");
  }

  // Contacts are not in the free PDF: each row links to the agent, which asks
  // the reader to sign in and then finds the manager, phone and who to ask for.
  function contactUrlForLead(lead) {
    return `${APP_URL}/?contact=${encodeURIComponent(lead.id)}`;
  }

  // "Why now" without the parts other columns already show (units, stage,
  // dates, buyer), so each fact appears once.
  const REPEATED_WHY = /^(\d[\d,]* units|sold\b|permitted$|planned$|under construction$|opens\b|expected\b|to )/i;

  function shortWhy(lead) {
    const parts = String(lead.why || lead.signal || "").split(/\s*·\s*/).filter((part) => part && !REPEATED_WHY.test(part));
    // The PDF font has no arrow, so "a → b" becomes "a, so b".
    const text = (parts.length ? parts.join(", ") : whyNowSentence(lead)).replace(/\s*→\s*/g, ", so ").replace(/\.$/, "");
    return text.charAt(0).toUpperCase() + text.slice(1) + ".";
  }

  function leadPackRows(leads) {
    return (leads || []).map((lead) => {
      const priority = priorityForLead(lead);
      const source = sourceForLead(lead);
      const units = lead.units == null ? "units not listed" : `${lead.units} units`;
      return {
        id: lead.id,
        priority,
        source,
        contactUrl: contactUrlForLead(lead),
        whyNow: whyNowSentence(lead),
        cells: [
          `${lead.property || lead.community || "Unnamed building"}\n${lead.city || "City not listed"} · ${units}`,
          `${priority.label} · ${Number(lead.score) || 0}`,
          stageForLead(lead),
          contactForLead(lead),
          shortWhy(lead),
          source.label,
        ],
      };
    });
  }

  function isoDate(value) {
    if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}/.test(value)) return value.slice(0, 10);
    const date = value instanceof Date ? value : new Date(value || Date.now());
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function displayDate(value) {
    const [year, month, day] = isoDate(value).split("-").map(Number);
    return new Intl.DateTimeFormat("en-US", { year: "numeric", month: "long", day: "numeric", timeZone: "UTC" })
      .format(new Date(Date.UTC(year, month - 1, day, 12)));
  }

  function slugifyRegion(region) {
    return String(region || "area")
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "area";
  }

  function filenameFor(region, date) {
    return `cranesignal-lead-pack-${slugifyRegion(region)}-${isoDate(date)}.pdf`;
  }

  function downloadDateKey(areaSlug, region) {
    return `${DOWNLOAD_DATE_KEY_PREFIX}:${encodeURIComponent(areaSlug || "area")}:${encodeURIComponent(region || "__all__")}`;
  }

  function lastDownloadDate(storage, areaSlug, region) {
    try {
      const value = storage && storage.getItem(downloadDateKey(areaSlug, region));
      return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : "";
    } catch (error) {
      return "";
    }
  }

  function rememberDownloadDate(storage, areaSlug, region, value) {
    const date = isoDate(value);
    try {
      if (storage) storage.setItem(downloadDateKey(areaSlug, region), date);
      return date;
    } catch (error) {
      return "";
    }
  }

  function leadsFirstSeenAfter(leads, date) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date || "")) return [];
    return (leads || []).filter((lead) => /^\d{4}-\d{2}-\d{2}$/.test(lead.firstSeen || "") && lead.firstSeen > date);
  }

  function buildLeadPack(options) {
    const opts = options || {};
    const JsPDF = opts.jsPDF || (root.jspdf && root.jspdf.jsPDF);
    if (!JsPDF) throw new Error("The PDF library did not load. Refresh the page and try again.");
    const doc = opts.doc || new JsPDF({ orientation: "landscape", unit: "pt", format: "letter", compress: true });
    const region = String(opts.region || "Selected area");
    const date = opts.date || new Date();
    const rows = leadPackRows(opts.leads || []);
    const title = `CraneSignal call list: ${region}, ${displayDate(date)}`;
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();

    doc.setProperties({
      title,
      subject: `${rows.length} apartment leads for ${region}`,
      author: "CraneSignal",
      creator: "CraneSignal call list",
      keywords: "apartment leads, property management software, CraneSignal",
    });
    doc.setFont("helvetica", "bold");
    doc.setFontSize(17);
    doc.setTextColor(14, 19, 32);
    doc.text(title, 30, 34);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(93, 101, 119);
    doc.text(`${rows.length} leads · One row per building · Free source links · Click \"Get who to call\" in a row and the CraneSignal agent finds the manager and who to ask for.`, 30, 51);

    const drawFooter = (pageNumber) => {
      doc.setFont("helvetica", "normal");
      doc.setFontSize(8);
      doc.setTextColor(26, 61, 143);
      doc.text(FOOTER, 30, pageHeight - 13);
      doc.link(30, pageHeight - 23, doc.getTextWidth(FOOTER), 14, { url: APP_URL });
      doc.setTextColor(93, 101, 119);
      doc.text(`Page ${pageNumber}`, pageWidth - 30, pageHeight - 13, { align: "right" });
    };

    const tableOptions = {
      startY: 64,
      head: [["Building", "Priority", "Stage", "Owner / phone / who to call", "Why now", "Source"]],
      body: rows.map((row) => row.cells),
      theme: "grid",
      margin: { top: 30, right: 30, bottom: 28, left: 30 },
      styles: {
        font: "helvetica",
        fontSize: 7.5,
        lineColor: [217, 220, 227],
        lineWidth: 0.5,
        cellPadding: 4,
        overflow: "linebreak",
        valign: "top",
        textColor: [52, 59, 76],
      },
      headStyles: {
        fillColor: [26, 61, 143],
        textColor: [255, 255, 255],
        fontStyle: "bold",
        fontSize: 8,
      },
      alternateRowStyles: { fillColor: [243, 244, 246] },
      columnStyles: {
        0: { cellWidth: 150, fontStyle: "bold", textColor: [14, 19, 32] },
        1: { cellWidth: 56 },
        2: { cellWidth: 100 },
        3: { cellWidth: 180 },
        4: { cellWidth: 150 },
        5: { cellWidth: 96, textColor: [26, 61, 143] },
      },
      rowPageBreak: "avoid",
      showHead: "everyPage",
      didParseCell(data) {
        if (data.section === "body" && data.column.index === 3) data.cell.styles.textColor = [26, 61, 143];
      },
      didDrawCell(data) {
        if (data.section !== "body") return;
        const row = rows[data.row.index];
        if (!row) return;
        if (data.column.index === 3) {
          doc.link(data.cell.x, data.cell.y, data.cell.width, data.cell.height, { url: row.contactUrl });
        }
        if (data.column.index === 5 && row.source && row.source.url) {
          doc.link(data.cell.x, data.cell.y, data.cell.width, data.cell.height, { url: row.source.url });
        }
      },
      didDrawPage(data) {
        drawFooter(data.pageNumber);
      },
    };

    if (typeof doc.autoTable === "function") {
      doc.autoTable(tableOptions);
    } else if (root.jspdfAutoTable && typeof root.jspdfAutoTable.autoTable === "function") {
      root.jspdfAutoTable.autoTable(doc, tableOptions);
    } else {
      throw new Error("The PDF table library did not load. Refresh the page and try again.");
    }

    return {
      doc,
      filename: filenameFor(region, date),
      rowCount: rows.length,
      rows,
      title,
    };
  }

  function downloadLeadPack(options) {
    const result = buildLeadPack(options);
    result.doc.save(result.filename);
    return result;
  }

  return {
    HOT_SCORE,
    WARM_SCORE,
    FOOTER,
    priorityForLead,
    phoneForLead,
    whyNowSentence,
    sourceForLead,
    leadPackRows,
    filenameFor,
    isoDate,
    displayDate,
    downloadDateKey,
    lastDownloadDate,
    rememberDownloadDate,
    leadsFirstSeenAfter,
    buildLeadPack,
    downloadLeadPack,
  };
});
