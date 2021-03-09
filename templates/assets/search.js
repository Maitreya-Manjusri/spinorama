Window.$ = window.jQuery;

$(document).ready(function () {
    
    window.$.getJSON("${site}/assets/metadata.json", function (response) {
	// console.log("got json")
	const metadata = Object.values(response);
	// console.log("got metadata")
	const fuse = new Fuse(metadata, {
	    isCaseSensitive: false,
	    matchAllTokens: true,
	    findAllMatches: true,
	    minMatchCharLength: 2,
	    keys: ["brand", "model"],
	    treshhold: 0.1,
	    distance: 2,
	    includeScore: true,
	    useExtendedSearch: true
	});
	
	const resultdiv = $("div.searchresults");
	
	let filter = {
	    reviewer: "",
	    shape: "",
	    power: "",
	    brand: "",
	};

	let sorter = {
	    by: "",
	};
	
	function selectDispatch(filter) {
	    let keywords = $("#searchInput").val();
	    // console.log("keywords: "+keywords)
	    if (keywords === "") {
		// console.log("display filter");
		display_filter(resultdiv, metadata, filter);
	    } else {
		// console.log("display search");
		let results = fuse.search(keywords);
		display_search(resultdiv, results, filter);
	    }
	}
	
	$("#selectReviewer").on("change", function () {
	    filter["reviewer"] = this.value;
	    selectDispatch(filter);
	});
	
	$("#selectShape").on("change", function () {
	    filter["shape"] = this.value;
	    selectDispatch(filter);
	});
	
	$("#selectPower").on("change", function () {
	    filter["power"] = this.value;
	    selectDispatch(filter);
	});
	
	$("#selectBrand").on("change", function () {
	    filter["brand"] = this.value;
	    selectDispatch(filter);
	});

	$("#sortBy").on("change", function () {
	    sorter["by"] = this.value;
	    selectDispatch(filter);
	    sortBy(sorter);
	});
	
	$("#searchInput").on("keyup", function () {
	    let keywords = $(this).val();
	    // console.log("search start "+keywords);
	    let results = fuse.search(keywords);
	    display_search(resultdiv, results, filter);
	});
	
	function is_filtered(item, filter) {
	    let show = true;
	    let default_measurement = item["default_measurement"];
	    let origin = item["measurements"][default_measurement]["origin"];
	    if (filter.reviewer !== "" ) {
		if (filter.reviewer === 'Vendors' ) {
		    if (origin.substr(0, 8) !== 'Vendors-' ) {
			console.log(origin.substr(0, 8));
			show = false;
		    }
		} else {
		    if (origin !== filter.reviewer) {
			show = false;
		    }
		}
	    }
	    if (filter.power !== "" && item.type !== filter.power) {
		show = false;
	    }
	    if (filter.shape !== "" && item.shape !== filter.shape) {
		show = false;
	    }
	    if (filter.brand !== "" && item.brand !== filter.brand) {
		show = false;
	    }
	    return show;
	}
	    
	function display_filter(resultdiv, meta, filter) {
	    console.log("display filter start");
	    for (const item in meta) {
		let show = is_filtered(meta[item], filter);
		const id = (meta[item].brand + "-" + meta[item].model).replace(/['.+& ]/g, "-");
		if (show) {
		    $("#" + id).show();
		} else {
		    $("#" + id).hide();
		}
	    }
	    resultdiv.show();
	}
	
	function display_search(resultdiv, results, filter) {
	    console.log("---------- display search start ----------------");
	    if (results.length === 0) {
		display_filter(resultdiv, metadata, filter);
		return;
	    }
	    // hide all
	    for (const item in metadata) {
		const id = (metadata[item].brand + "-" + metadata[item].model).replace(/['.+& ]/g, "-");
		$("#" + id).hide();
	    }
	    // minScore
	    let minScore = 1;
	    for (const item in results) {
		if (results[item].score < minScore) {
		    minScore = results[item].score;
		}
	    }
	    // console.log("minScore is "+minScore);
	    for (let item in results) {
		let show = true;
		let result = results[item];
		let meta = result.item;
		let score = result.score;
		console.log("evaluating "+meta.brand+" "+meta.model+" "+score);
		if (!is_filtered(meta, filter)) {
		    console.log("filtered out (filter)");
		    show = false;
		}
		if (show) {
		    if (minScore < Math.pow(10, -15)) {
                        // we have an exact match, only show other exact matches
                        if (score >= Math.pow(10, -15)) {
		            console.log("filtered out (minscore)" + score);
			    show = false;
                        }
		    } else {
                        // only partial match
                        if (score > minScore*10) {
		            console.log("filtered out (score="+score+"minscore="+minScore+")");
			    show = false;
			} 
		    }
		}
		const id = (meta.brand + "-" + meta.model).replace(/['.+& ]/g, "-");
		if (show) {
		    console.log("show "+meta.brand+" "+meta.model+" "+score);
		    $("#" + id).show();
		} else {
		    console.log("hide "+meta.brand+" "+meta.model+" "+score);
		    $("#" + id).hide();
		}
		
	    }
	    resultdiv.show();
	}

	function sortBy(sorter) {
	    // if (sorter["by"] !== "") {
	    // resultdiv = Object.fromEntries(
	    // Object.entries(resultdiv).sort(([,a],[,b]) => a-b)
	    // );
	    // }
	    resultdiv.show();
	}
	
    }).fail(function (jqXHR, textStatus) {
	console.log("getJSON request failed! " + textStatus);
    });
    
});

